"""`library` and `browse` served by the home server itself (0356).

A click on either used to stop the home server and start a container: 7.6 to 8.7 s
(measured on Windows, step 35 of `mh-measure.ps1`). Now the home server answers every
path not its own with the app of `library` (`search_app`), built at the first request,
again once the settings changed (`FreshRuntime`, 0358); no index: its pages say why.
"""

from __future__ import annotations

from contextlib import ExitStack, contextmanager
from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MountError
from media_hygiene.review.apply_relay import home_relay
from media_hygiene.review.home_paths import HOME_PATHS
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.http import ContentType, Response
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.events_desk import EVENTS_PAGE_PATH
from media_hygiene.search.folders import BROWSE_PATH
from media_hygiene.services.console_here import ReadOnlyHere
from media_hygiene.services.disk_here import DiskHere
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.pages_here import pages_here
from media_hygiene.services.places_here import PLACES_PREFIX, PlacesHere
from media_hygiene.services.review_here import ReviewHere
from media_hygiene.services.review_kinds import REVIEWS
from media_hygiene.services.search import open_search
from media_hygiene.services.search_app import SearchBuild, search_app
from media_hygiene.services.slideshow_here import SLIDESHOW_PREFIX, SlideshowHere
from media_hygiene.services.slideshow_selection import TvSlot

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from concurrent.futures import Executor

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.review.ending import Ending, Handling
    from media_hygiene.review.http import Request
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.search.app import SearchApp
    from media_hygiene.services.prefixed_page import ServedPage
    from media_hygiene.services.runtime import Runtime

_SEARCH_PAGES: Final = frozenset({SEARCH_PAGE_PATH, BROWSE_PATH, EVENTS_PAGE_PATH})


@dataclass(frozen=True, slots=True)
class HomeServer:
    """What the pages served by the home server share with it."""

    apply: Callable[[], ApplyStep | None] | None  # *Apply now*'s step; None: no button
    ending: Ending
    executor: Executor
    lan: LanAccess | None = None  # under `mh --lan`: the slideshow's phones and TVs
    tv: TvSlot = field(default_factory=TvSlot)  # 📺 On the TV of the pages (0454)


class SearchHere:
    """The app of `library` and `browse`, built once, at the first request of either."""

    def __init__(self, runtime: Runtime, server: HomeServer) -> None:
        """Remember how to build it.

        Args:
            runtime: Settings, mount points and output, at the server's start.
            server: The home server's *Apply now*, end and pool.
        """
        self._fresh = FreshRuntime(runtime)
        self._server = server
        self._stack = ExitStack()  # every index opened, closed with the server
        self._app: SearchApp | None = None
        self._built_for: Runtime | None = None
        self.refused: MountError | None = None  # why the last build failed

    def app(self) -> SearchApp | None:
        """The app, the index opened on the server's own thread: again on new settings.

        Returns:
            It; None while the cache holds no index (an audit makes one).
        """
        runtime = self._fresh.runtime()
        if self._app is not None and runtime is self._built_for:
            return self._app
        try:
            search = self._stack.enter_context(open_search(runtime, words=False))
        except MountError as error:
            self.refused = error
            return None
        self.refused = None
        server = self._server
        build = SearchBuild(
            SEARCH_PAGE_PATH,
            server.apply,
            server.ending,
            server.executor,
            home_relay(runtime.locations.reports_dir),
            server.tv,
        )
        self._app = search_app(runtime, search, build)
        self._built_for = runtime
        return self._app

    async def answer(self, request: Request, home: Handling) -> Response:
        """Answer with the app; without an index, its pages say why (never a 404).

        Args:
            request: The request.
            home: The home page's app, for every other path.

        Returns:
            The response.
        """
        app = self.app()
        if app is not None:
            return await app.handle(request)
        said = self.refused
        if said is None or request.path not in _SEARCH_PAGES:
            return await home.handle(request)
        text = "\n\n".join(filter(None, (said.message, said.tip, said.command)))
        return Response(HTTPStatus.SERVICE_UNAVAILABLE, text.encode(), ContentType.TEXT)

    def close(self) -> None:
        """Close the index, if it was opened."""
        self._stack.close()


@dataclass(frozen=True, slots=True)
class HomeWithPages:  # pylint: disable=too-many-instance-attributes
    """The home page's paths to the home page, every other one to `library`/`browse`."""

    home: Handling
    pages: SearchHere
    reviews: tuple[ReviewHere, ...]  # `/review/near/…` (0357), the others (0417)
    history: ReadOnlyHere  # `/history/` (0350), `/console/<step>/` (0567)
    slideshow: SlideshowHere  # `/slideshow/…`, its TV on the plain door (0417)
    places: PlacesHere  # `/places/…` (0417)
    disk: DiskHere  # `/disk-space/` (0539)
    more: tuple[ServedPage, ...]  # `/quarantine/`, `/import/` (0591, 0590)

    async def handle(self, request: Request) -> Response:
        """Route a request.

        Args:
            request: The request.

        Returns:
            The response.
        """
        path = request.path
        if path in HOME_PATHS or path.startswith(REPORTS_PREFIX):
            return await self.home.handle(request)
        served: tuple[ServedPage, ...] = (*self.reviews, self.disk, *self.more)
        page = next((each for each in served if each.serves(path)), None)
        if page is not None:
            return await page.handle(request)
        if path == PLACES_PREFIX or path.startswith(f"{PLACES_PREFIX}/"):
            return await self.places.handle(request)
        if path == SLIDESHOW_PREFIX or path.startswith(f"{SLIDESHOW_PREFIX}/"):
            return await self.slideshow.handle(request)
        if self.history.serves(path):
            return await self.history.handle(request)
        return await self.pages.answer(request, self.home)


@contextmanager
def home_with_pages(
    runtime: Runtime, home: Handling, server: HomeServer
) -> Iterator[HomeWithPages]:
    """The home page serving `library` and `browse` too, their index closed after.

    Args:
        runtime: Settings, mount points and output.
        home: The home page's app.
        server: The home server's *Apply now*, end and pool.

    Yields:
        The router.
    """
    pages = SearchHere(runtime, server)
    fresh = FreshRuntime(runtime)
    reviews = tuple(ReviewHere(kind, fresh, server) for kind in REVIEWS)
    slideshow = SlideshowHere(fresh, server)
    try:
        yield HomeWithPages(
            home,
            pages,
            reviews,
            ReadOnlyHere(fresh),
            slideshow,
            PlacesHere(fresh, server),
            DiskHere(fresh),
            pages_here(fresh, server.executor),
        )
    finally:
        slideshow.close()
        pages.close()
