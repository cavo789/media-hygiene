"""The slideshow served by the home server itself, under `/slideshow/` (0417).

*Show an album on the TV*, from the PC's home page or a paired phone (0444), used to end
the home server so that `mh` ran `slideshow --album <name> --lan`: the phone waited for
the new server, the TV paired again at every show. Now `GET /slideshow/album/<name>`
starts the album's show here and leads to its remote at once; the TVs (`Screens`) and
the pages waiting (`Changes`) belong to the home server, so a TV paired once stays
paired while it runs, and a new show reaches it by itself (its version is above the
last one's). The TV comes by the plain door at `/screen` (`tv`), no prefix there; `/`
of that door stays the certificate's steps for the phones. One show at a time: a new
album replaces the one shown.
"""

from __future__ import annotations

import dataclasses
from contextlib import ExitStack
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.album_show import ALBUM_SHOW, SLIDESHOW_PAGE
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan_ca_page import PHONE_STEPS
from media_hygiene.review.lan_phones import phone_book
from media_hygiene.services.search import open_search
from media_hygiene.services.slideshow import shown_slides
from media_hygiene.services.slideshow_build import Serving, show_app
from media_hygiene.services.slideshow_choices import Chooser
from media_hygiene.services.slideshow_pick import Pick
from media_hygiene.services.slideshow_selection import selected, why
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.door import Door, Visitor
from media_hygiene.slideshow.films import show_films
from media_hygiene.slideshow.screens import screens_of
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Timing
from media_hygiene.slideshow.tv_door import TV_HOME, TvDoor

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.slideshow.app import SlideshowApp

SLIDESHOW_PREFIX: Final = SLIDESHOW_PAGE.removesuffix("/")
_ALBUM_PATH: Final = f"/{ALBUM_SHOW}"
# The TV's page with no show yet asks again this often (a TV browser: a meta refresh).
_TV_WAIT_SECONDS: Final = 5
_TEMPLATES: Final = "media_hygiene.slideshow"


class SlideshowHere:
    """The show of the home server, and the TVs paired while it runs."""

    def __init__(self, fresh: FreshRuntime, server: HomeServer) -> None:
        """Start with no show; the TVs and the phones are those of the home server.

        Args:
            fresh: The server's settings, read again when their files change.
            server: The home server's pool and access to the home network.
        """
        self._fresh = fresh
        self._server = server
        lan = server.lan
        secure = lan is not None and lan.secure  # phones paired for good (0431)
        phones = phone_book(secure=secure)  # the TVs too, for good (0456)
        self.door = Door(lan, screens_of(phones), phones=phones)
        self._changes = Changes()
        self._stack = ExitStack()  # the index, opened at the first show
        self._search: tuple[SearchIndex, Runtime] | None = None
        self.app: SlideshowApp | None = None
        # 📺 On the TV of `search` and `browse` (0454)
        server.tv.start = partial(selected, self._begin)

    async def handle(self, request: Request) -> Response:
        """Answer a path under `/slideshow`, the prefix taken off.

        Args:
            request: The request, its path under the prefix.

        Returns:
            The show started, then its remote; 404 while none is shown.
        """
        path = request.path.removeprefix(SLIDESHOW_PREFIX)
        if not path:  # its paths are relative to `/slideshow/`
            location = f"Location: {SLIDESHOW_PAGE}"
            return Response(HTTPStatus.SEE_OTHER, headers=(location,))
        if request.method == "GET" and path.startswith(_ALBUM_PATH):
            return self._start(unquote(path.removeprefix(_ALBUM_PATH)))
        chosen = Chooser(self._opened, self._begin).answer(  # a folder, a month: 0455
            dataclasses.replace(request, path=path)
        )
        if chosen is not None:
            return chosen
        if self.app is None:
            message = _(
                "No slideshow is running: choose an album under Show an album on the "
                "TV, on the home page."
            )
            return Response(HTTPStatus.NOT_FOUND, message.encode())
        return await self.app.handle(dataclasses.replace(request, path=path))

    async def tv(self, request: Request) -> Response:
        """Answer the plain door: the TV's pages, the steps of the certificate at `/`.

        Args:
            request: A request of the plain door.

        Returns:
            The TV's page (one that waits while nothing is shown), its show, its
            pictures; 303 to the steps for `/`.
        """
        if request.path == TV_HOME:  # the phones' address (`lan_card`), not the TV's
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {PHONE_STEPS}",))
        if self.app is not None:
            return await TvDoor(self.app).handle(request)
        if self.door.tv_visitor(request) is Visitor.OUTSIDER:
            return Response(HTTPStatus.FORBIDDEN)
        environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
        page = environment.get_template("tv_wait.html.j2").render(
            refresh_seconds=_TV_WAIT_SECONDS
        )
        return Response(HTTPStatus.OK, page.encode(), ContentType.HTML)

    def _start(self, album: str) -> Response:
        """Start an album's show, in place of the one shown; then its remote.

        Args:
            album: The album's name, as saved.

        Returns:
            303 to the remote; 409 with the reason when there is nothing to show.
        """
        try:
            self._begin(Pick(album=album))
        except MediaHygieneError as exc:
            return Response(HTTPStatus.CONFLICT, why(exc).encode())
        return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {SLIDESHOW_PAGE}",))

    def _begin(self, pick: Pick) -> bool:
        """Start a show, in place of the one shown.

        On the server's own thread, as `search`: the index is opened there.

        Args:
            pick: What to show.

        Returns:
            Whether a show was running, now replaced.

        Raises:
            MediaHygieneError: Nothing to show.
        """
        runtime, search = self._opened()
        picked = shown_slides(runtime, search, pick)
        show = Show(picked.slides, Timing(runtime.settings.slideshow.interval_seconds))
        screens = self.door.screens
        replaced = self.app is not None
        if self.app is not None:  # the TVs waiting on the last show move on to this one
            show.version = self.app.desk.show.version + 1
        if not screens.films:
            show_films(show, films=False)
        desk = Desk(show, screens, self._changes)
        serving = Serving(
            search, self._server.executor, self.door, SLIDESHOW_PAGE, kept=True
        )
        self.app = show_app(runtime, desk, serving)
        self._changes.notify()
        return replaced

    def _opened(self) -> tuple[Runtime, SearchIndex]:
        """The settings now, and the index opened for them."""
        runtime = self._fresh.runtime()
        return runtime, self._index(runtime)

    def _index(self, runtime: Runtime) -> SearchIndex:
        """The index, opened once per settings.

        Args:
            runtime: The server's settings now.

        Returns:
            It.
        """
        if self._search is None or self._search[1] is not runtime:
            search = self._stack.enter_context(open_search(runtime, words=False))
            self._search = (search, runtime)
        return self._search[0]

    def close(self) -> None:
        """Close the index, if it was opened."""
        self._stack.close()
