"""`search` and `browse` served by the home server itself (0356).

A click on either from the home page used to stop the home server, start a container
for the page and wait for it: 7.6 to 8.7 s (measured on Windows, step 35 of
`mh-measure.ps1`). Now the home server answers them too: its own paths stay its own,
every other one goes to the app of `search` and `browse` (`search_app`), built at the
first request of either, the index opened once for the session. No path of theirs is
one of the home page's but `/` (read in the code): no prefix is needed for these two.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.review.home_app import AUDIT_PATH, STEP_PATH
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH
from media_hygiene.review.presence import PRESENCE_PATH
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.services.search import open_search
from media_hygiene.services.search_app import SearchBuild, search_app

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from concurrent.futures import Executor

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.review.ending import Ending, Handling
    from media_hygiene.review.http import Request, Response
    from media_hygiene.search.app import SearchApp
    from media_hygiene.services.runtime import Runtime

# The home page's own paths (`HomeApp`); `/reports/…` too.
_HOME_PATHS: Final = frozenset(
    {PAGE_PATH, STATE_PATH, STEP_PATH, AUDIT_PATH, PRESENCE_PATH}
)


@dataclass(frozen=True, slots=True)
class HomeServer:
    """What the pages served by the home server share with it."""

    apply: Callable[[], ApplyStep | None] | None  # *Apply now*'s step; None: no button
    ending: Ending
    executor: Executor


class SearchHere:
    """The app of `search` and `browse`, built once, at the first request of either."""

    def __init__(self, runtime: Runtime, server: HomeServer) -> None:
        """Remember how to build it.

        Args:
            runtime: Settings, mount points and output.
            server: The home server's *Apply now*, end and pool.
        """
        self._runtime = runtime
        self._server = server
        self._stack = ExitStack()
        self._app: SearchApp | None = None
        self._missing = False  # no index yet: answered by the home page, as before

    def app(self) -> SearchApp | None:
        """The app, the index opened on the server's own thread the first time.

        Returns:
            It; None when the cache holds no index yet.
        """
        if self._app is not None or self._missing:
            return self._app
        try:
            search = self._stack.enter_context(open_search(self._runtime, words=False))
        except MountError:
            self._missing = True
            return None
        server = self._server
        build = SearchBuild(
            SEARCH_PAGE_PATH, server.apply, server.ending, server.executor
        )
        self._app = search_app(self._runtime, search, build)
        return self._app

    def close(self) -> None:
        """Close the index, if it was opened."""
        self._stack.close()


@dataclass(frozen=True, slots=True)
class HomeWithPages:
    """The home page's paths to the home page, every other one to `search`/`browse`."""

    home: Handling
    pages: SearchHere

    async def handle(self, request: Request) -> Response:
        """Route a request.

        Args:
            request: The request.

        Returns:
            The response.
        """
        path = request.path
        if path in _HOME_PATHS or path.startswith(REPORTS_PREFIX):
            return await self.home.handle(request)
        app = self.pages.app()
        return await (self.home if app is None else app).handle(request)


@contextmanager
def home_with_pages(
    runtime: Runtime, home: Handling, server: HomeServer
) -> Iterator[HomeWithPages]:
    """The home page serving `search` and `browse` too, their index closed after.

    Args:
        runtime: Settings, mount points and output.
        home: The home page's app.
        server: The home server's *Apply now*, end and pool.

    Yields:
        The router.
    """
    pages = SearchHere(runtime, server)
    try:
        yield HomeWithPages(home, pages)
    finally:
        pages.close()
