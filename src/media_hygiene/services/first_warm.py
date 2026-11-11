"""Warm what the first clicks need once the home server listens (0677).

The library page's first opening cost imports, its template, the index opened and its
full-text table built, and a worker of the pool started: about 1.3 s on the demo. A
low-priority task runs the same reading requests a moment after the server listens,
through the server's own router, on its own thread (the index stays read-only); a
request the user already sent made them cheap. Nothing is written; the task is
cancelled with the server's loop, and any failure is left for the real request.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import ContentType, Request
from media_hygiene.search.app import SEARCH_PAGE_PATH, SEARCH_PATH

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor

    from media_hygiene.review.ending import Handling

WARM_DELAY: Final = 0.5  # seconds after the server listens: the home page shows first
_HOST: Final = {"host": "127.0.0.1"}
WARM_REQUESTS: Final = (
    Request("GET", SEARCH_PAGE_PATH, _HOST),
    Request(
        "POST",
        SEARCH_PATH,
        {**_HOST, "content-type": ContentType.JSON},
        b'{"text":""}',
    ),
)


def _nothing() -> None:
    """Run in a worker of the pool: starting it is the point."""


async def warm_first_clicks(router: Handling, pool: Executor) -> None:
    """Start a worker, then answer the library's first requests to nobody.

    Args:
        router: The server's router.
        pool: The server's pool (thumbnails, previews).
    """
    await asyncio.sleep(WARM_DELAY)
    with contextlib.suppress(Exception):  # the real request says what went wrong
        started = asyncio.wrap_future(pool.submit(_nothing))
        for request in WARM_REQUESTS:
            await router.handle(request)
            await asyncio.sleep(0)  # a real request waiting goes first
        await started


def warmed(
    ready: Callable[[int], None], router: Handling, pool: Executor
) -> Callable[[int], None]:
    """`ready`, then the warm-up started in the background.

    Args:
        ready: What the server says once it listens.
        router: The server's router.
        pool: The server's pool.

    Returns:
        The callback to give the server.
    """
    tasks: list[asyncio.Task[None]] = []  # a reference: the task is not collected

    def listening(port: int) -> None:
        """Say where the page is, then warm.

        Args:
            port: The port listened on.
        """
        ready(port)
        tasks.append(
            asyncio.get_running_loop().create_task(warm_first_clicks(router, pool))
        )

    return listening
