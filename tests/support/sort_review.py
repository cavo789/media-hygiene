"""The sort review without a browser: a classified library, its session, raw calls."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Request
from media_hygiene.review.sort_app import SortReviewApp
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.sort_reviewing import open_sort_review
from tests.support.runtime import make_runtime, thread_pool
from tests.support.sorting import build_library, classify

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.review.sort_session import SortSession
    from media_hygiene.services.runtime import Runtime

PAGE: Final = b"<!DOCTYPE html><title>sort review</title>"
PORT: Final = 4244
_JSON: Final = {"host": "127.0.0.1", "content-type": "application/json"}


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


def reopened(runtime: Runtime) -> SortReviewApp:
    """Open the review of the latest classify run, as the command does.

    Args:
        runtime: The runtime.

    Returns:
        Its app, previews rendered in-process.
    """
    return app_of(open_sort_review(runtime, None))


def app_of(session: SortSession) -> SortReviewApp:
    """Serve a session.

    Args:
        session: The review.

    Returns:
        Its app.
    """
    return SortReviewApp(session, PAGE, thread_pool())


async def call(app: SortReviewApp, route: str, body: object = None) -> Response:
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


async def first_event(app: SortReviewApp) -> tuple[str, list[str]]:
    """The first event of the review, and its rows.

    Args:
        app: The review.

    Returns:
        Its id and its row ids, in date order.
    """
    card = json.loads((await call(app, "GET /api/state")).body)["events"][0]
    view = json.loads((await call(app, f"GET /api/event/{card['id']}")).body)
    return card["id"], [photo["row"] for photo in view["photos"]]


def fake_server(action: Callable[[SortReviewApp], Awaitable[None]]) -> object:
    """A server that says it is ready, lets `action` act, then gets Ctrl+C.

    Args:
        action: What the browser does.

    Returns:
        A stand-in for `run_server`.
    """

    async def serve(
        app: SortReviewApp, _port: int, ready: Callable[[int], None]
    ) -> None:
        ready(PORT)
        await action(app)
        raise KeyboardInterrupt

    return serve
