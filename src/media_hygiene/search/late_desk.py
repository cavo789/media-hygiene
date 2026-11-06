"""*New photos during an event* (0558): late files on the pick grid, refusable.

`GET /api/late-events` lists the remembered events with files of their days arrived
later (the events page and the home page say "12 new photos during *Easter* — see
them?"); `GET /api/late-events/<rule name>` gives them as the search's tiles, each with
how it fits (`likely`: same camera ticked, another one unticked, another event's
camera proposed there, no camera asked). *Add* is the move of *Move to an event…*
(`move_go`, journaled, the event widened); `POST /api/late-events/refuse` writes the
picked files in `/config/events/<start>-<name>.toml`: never proposed again. Every
answer is read back from the disk.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.classify.event_files import add_refused
from media_hygiene.classify.late_files import (
    LateEvent,
    Likely,
    late_files,
    refused_by_event,
)
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import ngettext
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.event_match import label
from media_hygiene.search.events_desk import EVENTS_PAGE_PATH
from media_hygiene.search.late_aside import without_aside
from media_hygiene.search.late_tiles import late_tiles
from media_hygiene.search.sidecar_days import read_days_again

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.fts import SearchIndex

LATE_PATH: Final = "/api/late-events"
LATE_REFUSE_PATH: Final = f"{LATE_PATH}/refuse"
_MOST: Final = 20_000  # files refused at once, as *Move to an event…* takes


class Refusal(BaseModel):
    """The event, and the keys of the files it never takes."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    event: str = Field(min_length=1)
    keys: tuple[int, ...] = Field(min_length=1, max_length=_MOST)


@dataclass(frozen=True, slots=True)
class LateDesk:
    """Answers the late files of the remembered events."""

    index: SearchIndex
    mapper: HostPathMapper
    config_file: Path
    chosen: Callable[[], frozenset[str]]  # the host paths set aside

    def state(self, said: str = "") -> Response:
        """The events with late files, and how many of each kind.

        Args:
            said: What the last refusal wrote, read back.

        Returns:
            `{events: [{id, label, category, dates, total, probably, …}], said}`.
        """
        try:
            rules, found = self._found()
        except (ConfigError, ValueError) as exc:
            return json_response(HTTPStatus.OK, {"events": [], "error": str(exc)})
        listed = [
            {
                "id": event.rule.name,
                "label": label(event.rule, rules),
                "category": event.rule.category,
                "dates": event.rule.dates,
                "total": len(event.files),
                "page": f"{EVENTS_PAGE_PATH}?late={event.rule.name}",
                **{
                    kind.value: sum(file.likely is kind for file in event.files)
                    for kind in Likely
                },
            }
            for event in found
        ]
        return json_response(HTTPStatus.OK, {"events": listed, "said": said})

    def event(self, path: str) -> Response:
        """One event's late files, as the search's tiles.

        Args:
            path: `/api/late-events/<rule name>`.

        Returns:
            `{id, label, category, total, hits}`; 404 for an event without any.
        """
        wanted = unquote(path.removeprefix(f"{LATE_PATH}/"))
        try:
            rules, found = self._found()
        except ConfigError, ValueError:
            return Response(HTTPStatus.NOT_FOUND)
        event = next((item for item in found if item.rule.name == wanted), None)
        if event is None:
            return json_response(HTTPStatus.OK, {"id": wanted, "total": 0, "hits": []})
        names = {rule.name: label(rule, rules) for rule in rules}
        tiles = late_tiles(self.index, event, (self.mapper, self.chosen(), names))
        return json_response(
            HTTPStatus.OK,
            {
                "id": wanted,
                "label": names[wanted],
                "category": event.rule.category,
                **tiles,
            },
        )

    def refuse(self, body: bytes) -> Response:
        """Never propose the picked files to the event again.

        Args:
            body: `{event, keys}`.

        Returns:
            The list read back, with what was written; 400 for a bad body.
        """
        try:
            asked = Refusal.model_validate_json(body)
            rule = next(
                rule
                for rule in read_rules(self.config_file)
                if rule.name == asked.event
            )
        except (ValidationError, StopIteration, ConfigError, ValueError) as exc:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        ids = self._digests(asked.keys)
        try:
            held = add_refused(self.config_file, rule, ids)
        except ConfigError as exc:
            return json_response(HTTPStatus.CONFLICT, {"error": str(exc)})
        said = ngettext(
            "{count} photo refused: never proposed to this event again"
            " ({total} kept in {file}).",
            "{count} photos refused: never proposed to this event again"
            " ({total} kept in {file}).",
            len(ids & held),
        )
        linked = next(r for r in read_rules(self.config_file) if r.name == rule.name)
        return self.state(
            said.format(count=len(ids & held), total=len(held), file=linked.file)
        )

    def _found(self) -> tuple[tuple[ClassifyRule, ...], list[LateEvent]]:
        """The rules and the events with late files, those set aside left out.

        Returns:
            Both.
        """
        rules = read_rules(self.config_file)
        refused = refused_by_event(self.config_file.parent, rules)
        read_days_again(self.index.connection)  # a day set by hand counts (0618)
        found = late_files(self.index.connection, rules, refused)
        aside = (self.mapper, self.chosen())
        return rules, without_aside(self.index.connection, found, aside)

    def _digests(self, keys: tuple[int, ...]) -> set[str]:
        """The content ids of index keys.

        Args:
            keys: The keys.

        Returns:
            Their ids; a file not read yet has none.
        """
        query = "SELECT full_digest FROM files WHERE rowid = ?"
        execute = self.index.connection.execute
        return {
            str(row[0])
            for key in keys
            if (row := execute(query, (key,)).fetchone()) and row[0]
        }
