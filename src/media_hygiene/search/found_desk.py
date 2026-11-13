"""*Events found in your folders* (0557): the events sorted by hand, ticked to remember.

`GET /api/found-events` lists the folders `YYYY/YYYY-MM/<name>` of the index not yet
remembered (`proposed`, ticked on the page), those the user said are no event
(`not_events`, folded, can be ticked back) and the batches (`batches`: a gap longer
than `merge_gap_hours`, never proposed). `POST` the folders ticked and unticked: the
ticked ones become events of `events/<year>.toml` (0556's writer: name, period,
cameras), the unticked ones are remembered by content id in
`/config/events/not-events.toml`.
The answer is the list read back from the disk.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.classify.event_files import (
    add_not_events,
    read_not_events,
    take_back_not_events,
)
from media_hygiene.classify.found_folders import found_folders
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import ngettext
from media_hygiene.review.serving import json_response
from media_hygiene.search.event_match import Moved, events_named, joined_event
from media_hygiene.search.move_event import remember_event
from media_hygiene.search.sidecar_days import read_days_again
from media_hygiene.search.views import JPEG, THUMB_PREFIX
from media_hygiene.services.kept_state import (
    KeptState,
    connection_file,
    index_signature,
)

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.found_folders import FoundFolder
    from media_hygiene.config.classify_rules import ClassifyRule
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Response

FOUND_PATH: Final = "/api/found-events"
_SHOWN: Final = 4  # thumbnails per folder


class FoundChoice(BaseModel):
    """The folders ticked (events to remember) and unticked (no event)."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    ticked: tuple[str, ...] = ()
    unticked: tuple[str, ...] = ()


@dataclass(frozen=True, slots=True)
class FoundDesk:
    """Answers the list of the events found in the user's folders."""

    connection: sqlite3.Connection
    mapper: HostPathMapper
    config_file: Path
    reading: tuple[FolderRules, float]  # folder names' meaning, `merge_gap_hours`
    kept: KeptState[list[FoundFolder]] = field(default_factory=KeptState)

    def state(self, said: Sequence[str] = ()) -> Response:
        """The folders to tick, those said no event, the batches.

        Args:
            said: What the last confirmation wrote, read back.

        Returns:
            `{proposed, not_events, batches, said}`.
        """
        try:
            rules = read_rules(self.config_file)
            refused = read_not_events(self.config_file.parent)
        except (ConfigError, ValueError) as exc:
            return json_response(HTTPStatus.OK, {"proposed": [], "error": str(exc)})
        listed: dict[str, list[dict[str, object]]] = {
            "proposed": [],
            "not_events": [],
            "batches": [],
        }
        folders = self._folders()
        names = {found.name.casefold() for found in folders}
        for found in folders:
            if _known(found, rules, names):
                continue
            kind = (
                "not_events"
                if found.ids & refused
                else "proposed"
                if found.one_moment
                else "batches"
            )
            listed[kind].append(self._line(found))
        return json_response(HTTPStatus.OK, {**listed, "said": list(said)})

    def confirm(self, body: bytes) -> Response:
        """Remember the ticked folders as events, the unticked ones as no event.

        Args:
            body: `{ticked, unticked}`: folders (host paths) of the list.

        Returns:
            The list read back, with what was written; 400 for a bad body.
        """
        try:
            choice = FoundChoice.model_validate_json(body)
        except ValidationError as exc:
            return json_response(HTTPStatus.BAD_REQUEST, {"error": str(exc)})
        by_host = {self.mapper.to_host(Path(f.folder)): f for f in self._folders()}
        config_dir = self.config_file.parent
        said: list[str] = []
        for host in choice.ticked:
            if (found := by_host.get(host)) is None or not found.one_moment:
                continue
            take_back_not_events(config_dir, found.ids)
            moved = Moved(found.name, found.days, found.devices)
            said.append(remember_event(self.config_file, moved))
        refused = [by_host[h] for h in choice.unticked if h in by_host]
        if refused:
            add_not_events(config_dir, {i for found in refused for i in found.ids})
            said.append(
                ngettext(
                    "{count} folder remembered as no event.",
                    "{count} folders remembered as no event.",
                    len(refused),
                ).format(count=len(refused))
            )
        return self.state(said)

    def _folders(self) -> list[FoundFolder]:
        """The event folders of the index, kept while it and the days are the same.

        Returns:
            Them.
        """
        days = read_days_again(self.connection)  # a day set by hand counts (0618)
        index_file = connection_file(self.connection)
        return self.kept.value(
            lambda: (index_signature(index_file), sorted(days.items())),
            lambda: found_folders(self.connection, *self.reading),
        )

    def _line(self, found: FoundFolder) -> dict[str, object]:
        """One folder for the page.

        Args:
            found: The folder.

        Returns:
            Its host path, name, first and last day, files, cameras, thumbnails.
        """
        return {
            "folder": self.mapper.to_host(Path(found.folder)),
            "name": found.name,
            "first": found.days[0].isoformat(),
            "last": found.days[-1].isoformat(),
            "files": len(found.keys),
            "devices": list(found.devices),
            "thumbs": [f"{THUMB_PREFIX}{key}{JPEG}" for key in found.keys[:_SHOWN]],
        }


def _known(found: FoundFolder, rules: Sequence[ClassifyRule], names: set[str]) -> bool:
    """Tell a folder already remembered: an event of its name touching its days.

    A folder renamed in Explorer after acceptance (0556) is known too: an event of its
    days whose own name no folder holds any more.

    Args:
        found: The folder.
        rules: The rules of `config.toml`.
        names: The names of every folder found, casefolded.

    Returns:
        True when it is.
    """
    days = Moved(found.name, found.days)
    if joined_event(events_named(rules, found.name), days) is not None:
        return True
    lost = [
        rule
        for rule in rules
        if rule.match is RuleMatch.DATE_RANGE and rule.category.casefold() not in names
    ]
    return joined_event(lost, days) is not None
