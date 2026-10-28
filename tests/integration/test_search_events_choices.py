"""0438: the choices of the search's *🗂 Events* view, saved as review-sort did."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Request
from media_hygiene.search.events_choose import events_get, sort_post
from media_hygiene.search.events_desk import EVENTS_PATH, EventsDesk
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services.sort_reviewing import open_sort_review
from tests.support.sort_review import classified, saved_choices
from tests.support.sorting import EVENT_NAME

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

_JSON = {"host": "127.0.0.1", "content-type": "application/json"}


def _post(desk: EventsDesk | None, path: str, body: object) -> Response:
    """Post a choice to the Events view, as its page does."""
    request = Request("POST", path, _JSON, json.dumps(body).encode())
    return asyncio.run(sort_post(desk, request))


def test_a_choice_is_saved_with_the_workbook_value_seen(locations: Locations) -> None:
    """Named in the view: sort-decisions.json, read back; tiles say where they go."""
    runtime, workbook = classified(locations)
    with SearchIndex.open(locations.index_file) as search:
        desk = EventsDesk(
            search, runtime.mapper, lambda: open_sort_review(runtime, None), frozenset
        )
        [card] = json.loads(desk.state().body)["events"]
        view = json.loads(desk.event(f"{EVENTS_PATH}/{card['id']}").body)
        rows = [hit["row"] for hit in view["hits"]]
        assert all(rows)
        assert all(hit["movable"] for hit in view["hits"])
        named = _post(
            desk, "/api/sort/event", {"event": card["id"], "name": EVENT_NAME}
        )
        assert named.status == HTTPStatus.OK
        assert json.loads(named.body)["card"]["page"]["name"] == EVENT_NAME
        sent = {"event": card["id"], "rows": rows[:1], "stay": True}
        assert _post(desk, "/api/sort/files", sent).status == HTTPStatus.OK
        again = json.loads(desk.event(f"{EVENTS_PATH}/{card['id']}").body)
        assert again["hits"][0]["page"] == "(stay where it is)"
        forgot = _post(
            desk, "/api/sort/forget", {"event": card["id"], "rows": rows[:1]}
        )
        assert forgot.status == HTTPStatus.OK
        refused = _post(desk, "/api/sort/event", {"event": card["id"]})
        assert refused.status == HTTPStatus.UNPROCESSABLE_ENTITY
        _views_and_no_sorter(desk, card["id"])
    saved = saved_choices(workbook)
    [event] = saved.events
    assert (event.value.name, event.base.empty) == (EVENT_NAME, True)
    assert not saved.files  # taken back


def _views_and_no_sorter(desk: EventsDesk, event: str) -> None:
    """*Your rules* and the progress answer; no sorter: the GO is refused."""
    cannot = _post(desk, "/api/sort/sort-now", {"event": event})
    assert cannot.status == HTTPStatus.CONFLICT
    for path in ("/api/sort/progress", "/api/sort/rules"):
        answer = events_get(desk, path)
        assert answer is not None
        assert answer.status == HTTPStatus.OK
    assert events_get(desk, "/api/other") is None


def test_without_an_events_view_the_choices_are_not_found() -> None:
    """A page without the view: 404, never a traceback."""
    answer = _post(None, "/api/sort/event", {"event": "x"})
    assert answer.status == HTTPStatus.NOT_FOUND
    assert events_get(None, EVENTS_PATH) is None
