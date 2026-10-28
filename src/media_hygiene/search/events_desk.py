"""The *🗂 Events* view of the search (0437): the events of the latest classify plan.

Read-only for now: `GET /api/events` lists the events of the plan (its workbook and the
page's earlier choices laid over, as review-sort shows them) with the progress;
`GET /api/events/<id>` one event's card and its photos, as the search's own tiles (the
index's keys: the same previews, large view and set aside). The plan is read on the
first ask, not when the search starts: a search never waits for a workbook.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import DecisionsError, MediaHygieneError
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.hits import hit_of, with_facts
from media_hygiene.search.models import Found
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.review.sort_cards import PhotoCard
    from media_hygiene.search.fts import SearchIndex

EVENTS_PAGE_PATH: Final = "/events"
EVENTS_PATH: Final = "/api/events"
_ROWS: Final = (
    f"SELECT rowid, path, size, mtime_ns, {DAY}(media_date) FROM files"  # noqa: S608
    " WHERE path IN ({marks})"
)


@dataclass(frozen=True, slots=True)
class EventsDesk:
    """Answers the Events view: the plan's events, one event's photos."""

    index: SearchIndex
    mapper: HostPathMapper
    opener: Callable[[], SortBatchSession]  # raises when there is no plan to read
    chosen: Callable[
        [], frozenset[str]
    ]  # the host paths set aside, marked on the tiles
    held: list[SortBatchSession] = field(default_factory=list)  # opened once

    def state(self) -> Response:
        """The events of the plan and the progress, or why there are none.

        Returns:
            `{workbook, decisions, events, progress}`, or `{events: [], missing}`.
        """
        try:
            session = self._session()
        except MediaHygieneError as exc:
            return json_response(HTTPStatus.OK, {"events": [], "missing": str(exc)})
        state = session.state().model_dump(mode="json")
        progress = session.progress_view().model_dump(mode="json")
        return json_response(HTTPStatus.OK, {**state, "progress": progress})

    def event(self, path: str) -> Response:
        """One event: its card and its photos, as the search's tiles.

        Args:
            path: `/api/events/<id>`.

        Returns:
            `{card, hits, missing}` (photos the index does not hold); 404 for an
            unknown event or no plan.
        """
        try:
            view = self._session().event(path.removeprefix(f"{EVENTS_PATH}/"))
        except DecisionsError, MediaHygieneError:
            return Response(HTTPStatus.NOT_FOUND)
        found = self._tiles(view.photos)
        return json_response(
            HTTPStatus.OK,
            {
                "card": view.card.model_dump(mode="json"),
                **found_view(found, self.mapper, self.chosen()),
                "missing": len(view.photos) - found.total,
            },
        )

    def _tiles(self, photos: tuple[PhotoCard, ...]) -> Found:
        """The photos of an event, found in the index, in the event's order.

        Args:
            photos: Its photos.

        Returns:
            Those the index holds, described as a search describes them.
        """
        paths = [
            str(PurePosixPath(self.mapper.to_container(photo.folder)) / photo.name)
            for photo in photos
        ]
        rows = (
            self.index.connection.execute(
                _ROWS.format(marks=", ".join("?" * len(paths))), paths
            ).fetchall()
            if paths
            else []
        )
        by_path = {str(row[1]): row for row in rows}
        hits = tuple(
            hit_of((None, {}), by_path[path]) for path in paths if path in by_path
        )
        return with_facts(self.index, Found(len(hits), hits))

    def _session(self) -> SortBatchSession:
        """The plan's session, opened on the first ask.

        Returns:
            It.
        """
        if not self.held:
            self.held.append(self.opener())
        return self.held[0]
