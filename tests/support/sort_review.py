"""The sort choices without a browser: a classified library, its session, raw calls.

Review-sort's page is gone (0439): its choices answer on the search's *🗂 Events* view
(`search/events_choose`, `/api/sort/…`). `EventsPage` takes review-sort's routes as the
tests send them (`POST /api/event`) and answers through those of the search page.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, cast

from media_hygiene.classify.page_decisions import PageDecisions, read_page_decisions
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.scan.progress import NullProgress
from media_hygiene.search.events_choose import (
    SORT_GETS,
    SORT_POSTS,
    events_get,
    sort_path,
    sort_post,
)
from media_hygiene.search.events_desk import EventsDesk
from media_hygiene.services.audit import AuditService
from media_hygiene.services.sort_reviewing import open_sort_review
from tests.support.runtime import make_runtime
from tests.support.sorting import build_library, classify

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.review.sort_now import Sorter
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

PORT: Final = 4244
_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}
_EVENT: Final = "/api/event/"


@dataclass(frozen=True, slots=True)
class EventsPage:
    """Review-sort's routes, answered by the search's Events view."""

    session: SortBatchSession
    sorter: Sorter | None = None

    async def handle(self, request: Request) -> Response:
        """Answer one of review-sort's routes through the search's.

        Args:
            request: `GET /api/state`, `POST /api/event`…

        Returns:
            The search's answer; 404 for a route it does not have.
        """
        desk = EventsDesk(
            cast("SearchIndex", None),
            cast("HostPathMapper", None),
            lambda: self.session,
            frozenset,
            lambda _session: self.sorter,
        )
        path = sort_path(request.path)
        if request.method == "POST" and path in SORT_POSTS:
            moved = Request(request.method, path, request.headers, request.body)
            return await sort_post(desk, moved)
        if path in SORT_GETS:
            return cast("Response", events_get(desk, path))
        if request.path == "/api/state":
            return _json(self.session.state().model_dump_json())
        if request.path.startswith(_EVENT):
            try:
                view = self.session.event(request.path.removeprefix(_EVENT))
            except MediaHygieneError:
                return Response(HTTPStatus.NOT_FOUND)
            return _json(view.model_dump_json())
        return Response(HTTPStatus.NOT_FOUND)


def _json(text: str) -> Response:
    """A JSON answer.

    Args:
        text: The JSON.

    Returns:
        It, 200.
    """
    return Response(HTTPStatus.OK, text.encode(), ContentType.JSON)


def classified(locations: Locations) -> tuple[Runtime, Path]:
    """Write the small library of `sorting`, audit it, classify it.

    Args:
        locations: The test mount points.

    Returns:
        The runtime and the workbook.
    """
    build_library(locations.data_dir)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    return runtime, classify(runtime)


def reopened(runtime: Runtime) -> EventsPage:
    """Open the review of the latest classify run, as the command does.

    Args:
        runtime: The runtime.

    Returns:
        Its app, previews rendered in-process.
    """
    return app_of(open_sort_review(runtime, None))


def app_of(session: SortBatchSession, sorter: Sorter | None = None) -> EventsPage:
    """Serve a session.

    Args:
        session: The review.
        sorter: *Sort this event now*; None: the page cannot move files.

    Returns:
        Its routes.
    """
    return EventsPage(session, sorter)


async def call(app: EventsPage, route: str, body: object = None) -> Response:
    """Send one request to the app, as the page does; `route`: `GET /api/state`.

    Args:
        app: The app.
        route: Method and path.
        body: The JSON body, if any.

    Returns:
        The response.
    """
    method, path = route.split()
    headers = _JSON if body is not None else {"host": "127.0.0.1"}
    data = json.dumps(body).encode() if body is not None else b""
    return await app.handle(Request(method, path, headers, data))


async def first_event(app: EventsPage) -> tuple[str, list[str]]:
    """The first event of the review, and its rows.

    Args:
        app: The review.

    Returns:
        Its id and its row ids, in date order.
    """
    card = json.loads((await call(app, "GET /api/state")).body)["events"][0]
    view = json.loads((await call(app, f"GET /api/event/{card['id']}")).body)
    return card["id"], [photo["row"] for photo in view["photos"]]


def fake_server(action: Callable[[EventsPage], Awaitable[None]]) -> object:
    """A server that says it is ready, lets `action` act, then gets Ctrl+C.

    Args:
        action: What the browser does.

    Returns:
        A stand-in for `run_server`.
    """

    async def serve(app: EventsPage, _port: int, ready: Callable[[int], None]) -> None:
        ready(PORT)
        await action(app)
        raise KeyboardInterrupt

    return serve


def saved_choices(workbook: Path) -> PageDecisions:
    """The page's choices, read back from `sort-decisions.json` next to the plan.

    Args:
        workbook: The classify workbook.

    Returns:
        Them.
    """
    plan = ClassifyPlan.model_validate_json(
        workbook.with_name("plan.json").read_text("utf-8")
    )
    return read_page_decisions(workbook.with_name("sort-decisions.json"), plan.plan_id)
