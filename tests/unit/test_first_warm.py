"""The warm-up of the first clicks after the home server listens (0677)."""

from __future__ import annotations

import asyncio
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Request, Response
from media_hygiene.search.app import SEARCH_PAGE_PATH, SEARCH_PATH
from media_hygiene.services import first_warm
from media_hygiene.services.first_warm import WARM_REQUESTS, warmed

if TYPE_CHECKING:
    import pytest


async def _serve(handled: list[Request], fails: bool = False) -> list[int]:  # noqa: FBT001, FBT002
    """Start the warm-up as the server would and let it run.

    Args:
        handled: Receives each request the warm-up sent.
        fails: The router raises.

    Returns:
        The ports `ready` was told.
    """
    told: list[int] = []

    class Router:
        """Records what it is asked."""

        async def handle(self, request: Request) -> Response:
            """Record a request.

            Args:
                request: The request.

            Returns:
                200.

            Raises:
                RuntimeError: When asked to fail.
            """
            handled.append(request)
            if fails:
                raise RuntimeError
            return Response(HTTPStatus.OK)

    with ThreadPoolExecutor(1) as pool:
        warmed(told.append, Router(), pool)(1234)
        await asyncio.sleep(0.05)
    return told


def test_ready_first_then_the_library_requests(monkeypatch: pytest.MonkeyPatch) -> None:
    """The server's message goes first; the page and an empty search follow."""
    monkeypatch.setattr(first_warm, "WARM_DELAY", 0.0)
    handled: list[Request] = []
    assert asyncio.run(_serve(handled)) == [1234]
    assert [(each.method, each.path) for each in handled] == [
        ("GET", SEARCH_PAGE_PATH),
        ("POST", SEARCH_PATH),
        ("GET", "/api/folders"),  # the kept states built ahead (0804)
        ("GET", "/api/found-events"),
        ("GET", "/places/"),
    ]
    assert handled == list(WARM_REQUESTS)


def test_a_failure_leaves_no_trace(monkeypatch: pytest.MonkeyPatch) -> None:
    """A router that raises stops the warm-up silently: the real request tells."""
    monkeypatch.setattr(first_warm, "WARM_DELAY", 0.0)
    handled: list[Request] = []
    asyncio.run(_serve(handled, fails=True))
    assert len(handled) == 1


def test_stopped_before_it_starts() -> None:
    """A server stopping during the delay cancels the warm-up: nothing is sent."""
    handled: list[Request] = []
    asyncio.run(_serve(handled))
    assert not handled
