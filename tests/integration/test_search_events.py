"""0437: the search's *🗂 Events* view lists the plan's events and shows one's photos."""

from __future__ import annotations

import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.errors import MediaHygieneError
from media_hygiene.search.events_desk import EVENTS_PATH, EventsDesk
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services.sort_reviewing import open_sort_review
from tests.support.sort_review import classified

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.sort_batch import SortBatchSession

_NO_PLAN = "no plan"


def _nothing_chosen() -> frozenset[str]:
    """No file set aside.

    Returns:
        None.
    """
    return frozenset()


def test_the_events_and_one_event_as_search_tiles(locations: Locations) -> None:
    """The state lists every event with the progress; an event's photos are tiles."""
    runtime, _workbook = classified(locations)
    opened: list[int] = []

    def opener() -> SortBatchSession:
        opened.append(1)
        return open_sort_review(runtime, None)

    with SearchIndex.open(locations.index_file) as search:
        desk = EventsDesk(search, runtime.mapper, opener, _nothing_chosen)
        state = json.loads(desk.state().body)
        assert state["events"]
        assert "sorted_files" in state["progress"]["progress"]
        card = state["events"][0]
        answer = desk.event(f"{EVENTS_PATH}/{card['id']}")
        assert answer.status == HTTPStatus.OK
        view = json.loads(answer.body)
        assert view["card"]["id"] == card["id"]
        assert view["missing"] == 0
        assert len(view["hits"]) == card["files"]
        tile = view["hits"][0]
        assert tile["thumb"].startswith("/thumb/")
        assert tile["chosen"] is False
        assert desk.event(f"{EVENTS_PATH}/nope").status == HTTPStatus.NOT_FOUND
    assert len(opened) == 1  # the plan is read once


def test_without_a_plan_the_view_says_why(locations: Locations) -> None:
    """No classify run: no event, the reason, and a 404 for any event."""
    runtime, _workbook = classified(locations)

    def opener() -> SortBatchSession:
        raise MediaHygieneError(_NO_PLAN)

    with SearchIndex.open(locations.index_file) as search:
        desk = EventsDesk(search, runtime.mapper, opener, _nothing_chosen)
        assert json.loads(desk.state().body) == {"events": [], "missing": _NO_PLAN}
        assert desk.event(f"{EVENTS_PATH}/x").status == HTTPStatus.NOT_FOUND
