"""Warm what the first clicks need once the home server listens (0677).

The library page's first opening cost imports, its template, the index opened and its
full-text table built, and a worker of the pool started: about 1.3 s on the demo. A
low-priority task runs the same reading requests a moment after the server listens,
through the server's own router, on its own thread (the index stays read-only); a
request the user already sent made them cheap. The folder tree, *Events found* and
the map are built too, and kept by their pages until something changes (0804). The
people page comes last (0817): its build writes its face groups, as a visit would, so
it is skipped while another connection writes the index (an audit, `people`), and
while nobody is named yet (its 95 MB and 2.5 s spent for a page maybe never opened):
the visit builds it then. The task is cancelled with the server's loop, and any failure
is left for the real request.
"""

from __future__ import annotations

import asyncio
import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.loader import load_settings
from media_hygiene.errors import ConfigError
from media_hygiene.index.write_probe import index_busy
from media_hygiene.paths.locations import Locations
from media_hygiene.review.http import ContentType, Request
from media_hygiene.review.step_watch import PLACES_PAGE
from media_hygiene.search.app import SEARCH_PAGE_PATH, SEARCH_PATH
from media_hygiene.search.folders import FOLDERS_PATH
from media_hygiene.search.found_desk import FOUND_PATH
from media_hygiene.services.people_here import PEOPLE_PAGE

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
    # Kept by their pages while nothing changes (0804): the first click is warm too.
    Request("GET", FOLDERS_PATH, _HOST),
    Request("GET", FOUND_PATH, _HOST),
    Request("GET", PLACES_PAGE, _HOST),
)
# Kept too, but its build writes into the index: last, never beside a writer (0817).
WARM_PEOPLE: Final = Request("GET", PEOPLE_PAGE, _HOST)


def _nothing() -> None:
    """Run in a worker of the pool: starting it is the point."""


def people_worth_warming() -> bool:
    """Tell whether the people page should be built ahead now.

    Returns:
        True when someone is named and no other connection writes the index (an
        audit, `people`); False too when the settings or the index cannot be read.
    """
    locations = Locations()
    try:
        named = bool(load_settings(locations).settings.people.person)
    except ConfigError, OSError:  # the visit says what is wrong
        return False
    return named and not index_busy(locations.index_file)


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
        if await asyncio.to_thread(people_worth_warming):
            await router.handle(WARM_PEOPLE)
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
