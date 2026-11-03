"""The *🗂 Events* tab without any classify plan (0572): events made from the index.

The files not sorted yet (`Sorting.LEFT`, the search's own condition: not in a
`YYYY/YYYY-MM/<name>` folder, whoever moved them) of the period shown, in the order
they were taken, cut where no photo was taken for `classify`'s longest gap
(`event_gap_hours`), without rules nor AI. Made on each ask, never stored: a file
moved since is simply no longer listed.

`GET /api/events/span/<from>..<to>` lists them (either day may be empty);
`GET /api/events/files/<first>..<last>` gives the tiles of one, as the search's. An
event the user chose not to sort (0574, `span_left`) is listed with `left`.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from media_hygiene.classify.event_left import read_left
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.hits import hit_of, with_facts
from media_hygiene.search.models import Found
from media_hygiene.search.span_cards import BETWEEN, Row, card_of, when_taken
from media_hygiene.search.statements import AND, DAYS, LEFT_OR_NOT
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.search.fts import SearchIndex

SPAN_PATH: Final = "/api/events/span/"
SPAN_FILES_PATH: Final = "/api/events/files/"
# The same condition as the search's *Not sorted yet* (`Sorting.LEFT`), never a copy.
_LEFT: Final = (
    f"SELECT rowid, path, size, mtime_ns, {DAY}(media_date), media_date,"  # noqa: S608
    " full_digest"
    f" FROM files WHERE {DAY}(media_date) IS NOT NULL AND {LEFT_OR_NOT}"
)


@dataclass(frozen=True, slots=True)
class SpanEvents:
    """Answers the Events tab from the index alone: the events, one event's tiles."""

    index: SearchIndex
    mapper: HostPathMapper
    chosen: Callable[[], frozenset[str]]  # the host paths set aside
    gap_hours: float  # `classify`'s longest gap (`event_gap_hours`)
    config_dir: Path | None = None  # where `events/left.toml` lies (0574)

    def answer(self, path: str) -> Response:
        """The events of a period, or the tiles of one event.

        Args:
            path: `SPAN_PATH<from>..<to>` or `SPAN_FILES_PATH<first>..<last>`.

        Returns:
            `{events}` or the search's tiles; 404 for a period that is not one.
        """
        listing = path.startswith(SPAN_PATH)
        bounds = unquote(path.removeprefix(SPAN_PATH if listing else SPAN_FILES_PATH))
        first, between, last = bounds.partition(BETWEEN)
        try:
            if listing and between:
                return self._events(first, last)
            if between and first and last:
                return self._files(datetime.fromisoformat(first), last)
        except ValueError:
            pass
        return Response(HTTPStatus.NOT_FOUND)

    def _events(self, first: str, last: str) -> Response:
        """The events of the files not sorted yet of these days.

        Args:
            first: The first day (`YYYY-MM-DD`), or empty: no lower bound.
            last: The last day, or empty.

        Returns:
            `{events: [{id, first, last, files, folders}]}`, oldest first.
        """
        held = read_left(self.config_dir) if self.config_dir else frozenset()
        events = [
            card_of(group, self.mapper, held) for group in self.groups(first, last)
        ]
        return json_response(HTTPStatus.OK, {"events": events})

    def groups(self, first: str, last: str) -> list[list[tuple[datetime, Row]]]:
        """The files not sorted yet of these days, cut at each long gap.

        Args:
            first: The first day, or empty.
            last: The last day, or empty.

        Returns:
            The events, oldest first, each one's files in the order taken.
        """
        timed = sorted(
            ((when_taken(row), row) for row in self._rows(first, last)),
            key=lambda pair: (pair[0], pair[1][1]),
        )
        gap = timedelta(hours=self.gap_hours)
        groups: list[list[tuple[datetime, Row]]] = []
        for pair in timed:
            if groups and pair[0] - groups[-1][-1][0] <= gap:
                groups[-1].append(pair)
            else:
                groups.append([pair])
        return groups

    def _files(self, start: datetime, last: str) -> Response:
        """The tiles of one event: its files not sorted yet, in the order taken.

        Args:
            start: When its first file was taken.
            last: When its last one was, ISO.

        Returns:
            The search's tiles of these files.
        """
        rows = self.event_rows(start, datetime.fromisoformat(last))
        hits = tuple(hit_of((None, {}), row[:5]) for row in rows)
        found = with_facts(self.index, Found(len(hits), hits))
        return json_response(
            HTTPStatus.OK, found_view(found, self.mapper, self.chosen())
        )

    def event_rows(self, start: datetime, end: datetime) -> list[Row]:
        """The files not sorted yet of one event, in the order taken.

        Args:
            start: When its first file was taken.
            end: When its last one was.

        Returns:
            Their rows.
        """
        return [
            row
            for when, row in sorted(
                (when_taken(row), row)
                for row in self._rows(start.date().isoformat(), end.date().isoformat())
            )
            if start <= when <= end
        ]

    def _rows(self, first: str, last: str) -> list[Row]:
        """The dated files not sorted yet of these days.

        Args:
            first: The first day, or empty.
            last: The last day, or empty.

        Returns:
            Their rows: key, path, size, mtime, day and date as written.
        """
        statement, parameters = _LEFT, list[object]([1])
        if first or last:
            statement += AND + DAYS
            parameters += [first or "0000-00-00", last or "9999-99-99"]
        return self.index.connection.execute(statement, parameters).fetchall()
