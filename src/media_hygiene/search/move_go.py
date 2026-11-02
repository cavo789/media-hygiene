"""*Move to an event…* (0403): the photos picked, shown by source folder, then moved.

`POST /api/move/view` answers where the keys picked would go for the name typed (or
the one proposed), grouped by source folder, each ticked or not; `POST /api/move`
moves the keys ticked to `YYYY/YYYY-MM/<name>` in a thread (`services.selection_move`,
the journaled sort of a group), and answers the run read back, the event remembered
in `config.toml` on the same action (`move_event`, 0556).
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.classify.dates import exif_datetime, video_date, zone_of
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.search import statements as sql
from media_hygiene.search.aside_filter import AsideFilter
from media_hygiene.search.event_match import Moved
from media_hygiene.search.move_event import cameras_of, foreseen, remember_event
from media_hygiene.search.rule_models import refused_rule
from media_hygiene.services.selection_models import Picked, event_path

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.search.rule_desk import RuleDesk

MOVE_VIEW_PATH: Final = "/api/move/view"
MOVE_PATH: Final = "/api/move"
_MOST: Final = 20_000  # photos picked at once: a few years of a family
_LONGEST: Final = 200  # characters of a folder name: Windows' limit is the whole path


class MoveIn(BaseModel):
    """The keys picked (or ticked), and the event's name typed."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    keys: tuple[int, ...] = Field(min_length=1, max_length=_MOST)
    name: str = Field(default="", max_length=_LONGEST)


async def move_answer(desk: RuleDesk, path: str, body: bytes) -> Response:
    """Show where the photos picked would go, or move those ticked.

    Args:
        desk: The rule's desk: the index and the mover.
        path: `MOVE_VIEW_PATH` or `MOVE_PATH`.
        body: The keys and the name.

    Returns:
        The view, or the run read back; 400 for a body that cannot be read, 409 with
        the sentence to show when nothing can move.
    """
    try:
        asked = MoveIn.model_validate_json(body)
    except ValidationError as exc:
        return refused_rule(exc)
    if desk.mover is None:
        return _conflict(_("This page cannot move files: run 'sort' in the terminal."))
    chosen, ignored = _picked(desk, asked.keys)
    try:
        if path == MOVE_VIEW_PATH:
            view = await asyncio.to_thread(desk.mover.view, chosen, asked.name)
            answer: dict[str, object] = view.model_dump()
            answer["remembers"] = foreseen(
                _config_of(desk), _moved(desk, view.name, chosen)
            )
        else:
            answer = await asyncio.to_thread(desk.mover.move, chosen, asked.name)
            desk.index.built = None  # this page moved files: its next search reads them
            moved = _moved(desk, event_path(asked.name), chosen)
            answer["remembered"] = remember_event(_config_of(desk), moved)
    except ValueError as exc:
        return _conflict(" ".join(filter(None, (str(exc), ignored))))
    except MediaHygieneError as exc:
        return _conflict(" ".join(filter(None, (exc.message, exc.tip, ignored))))
    answer["ignored"] = ignored  # the files set aside left out (0518)
    return json_response(HTTPStatus.OK, answer)


def _picked(desk: RuleDesk, keys: tuple[int, ...]) -> tuple[Picked, str]:
    """The files of the keys picked, and when each was taken as the index reads it.

    The files set aside are left out: gone for a move, whatever picked them (0518).

    Args:
        desk: The rule's desk: the index.
        keys: The keys, from the page.

    Returns:
        Them: a photo or video the classify plan lacks still has its month; the
        sentence on the files set aside left out.
    """
    connection = desk.index.connection
    paths: dict[int, Path] = {}
    days: dict[Path, datetime] = {}
    zone = zone_of(desk.mover.runtime.settings.classify.timezone if desk.mover else "")
    found = {key: hit.path for key in keys if (hit := desk.index.source_of(key))}
    kept = AsideFilter(desk.aside, desk.mapper).keep(found.values())
    for key, path in found.items():
        if path not in kept.files:
            continue
        paths[key] = path
        row = connection.execute(sql.DATE_OF, (key,)).fetchone()
        written = row[0] if row else None
        if when := exif_datetime(written) or video_date(written, zone):  # a video: ISO
            days[path] = when
    return Picked(paths, days), kept.said


def _moved(desk: RuleDesk, name: str, chosen: Picked) -> Moved:
    """What a move brings to its event: the name, the days, the cameras.

    Args:
        desk: The rule's desk: the index.
        name: The event's folder name.
        chosen: The files picked and their dates.

    Returns:
        The move.
    """
    days = tuple(sorted(when.date() for when in chosen.days.values()))
    devices = cameras_of(desk.index.connection, tuple(chosen.paths))
    return Moved(name, days, devices)


def _config_of(desk: RuleDesk) -> Path:
    """`config.toml`, where the event is remembered.

    Args:
        desk: The rule's desk: the mover's runtime.

    Returns:
        Its path.
    """
    if desk.mover is None:  # pragma: no cover - checked before any move
        raise MediaHygieneError(
            _("This page cannot move files: run 'sort' in the terminal.")
        )
    return desk.mover.runtime.locations.config_file


def _conflict(said: str) -> Response:
    """Answer that nothing moved, and why.

    Args:
        said: The sentence to show.

    Returns:
        409, with it.
    """
    return json_response(HTTPStatus.CONFLICT, {"error": said})
