"""*Move to an event…* (0403): the photos picked, shown by source folder, then moved.

`POST /api/move/view` answers where the keys picked would go for the name typed (or
the one proposed), grouped by source folder, each ticked or not; `POST /api/move`
moves the keys ticked to `YYYY/YYYY-MM/<name>` in a thread (`services.selection_move`,
the journaled sort of a group), and answers the run read back. No rule is written: a
selection with exceptions is a move, not a rule.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.config.rule_checks import one_name
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response
from media_hygiene.search.rule_models import refused_rule

if TYPE_CHECKING:
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
    chosen: dict[int, Path] = {
        key: found.path for key in asked.keys if (found := desk.index.source_of(key))
    }
    try:
        if path == MOVE_VIEW_PATH:
            view = await asyncio.to_thread(desk.mover.view, chosen, asked.name)
            answer: dict[str, object] = view.model_dump()
        else:
            name = one_name(asked.name)
            answer = await asyncio.to_thread(desk.mover.move, chosen, name)
    except ValueError as exc:
        return _conflict(str(exc))
    except MediaHygieneError as exc:
        return _conflict(" ".join(filter(None, (exc.message, exc.tip))))
    return json_response(HTTPStatus.OK, answer)


def _conflict(said: str) -> Response:
    """Answer that nothing moved, and why.

    Args:
        said: The sentence to show.

    Returns:
        409, with it.
    """
    return json_response(HTTPStatus.CONFLICT, {"error": said})
