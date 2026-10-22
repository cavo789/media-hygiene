"""The routes of the slideshow: the screen for the TV, the remote for the phone.

- `GET /screen`: the TV's page (any visitor but an outsider; a stranger gets a token
  in a cookie, then shows its code). `GET /api/wait/<version>`: what the TV shows,
  once the show is past that version (a long poll): the picture, the next one to load
  in advance, or the code to type on the phone while not paired.
- `GET /`: the remote; `GET /api/slides`: the photos; `GET /api/show/<version>`: the
  show once past that version; `POST /api/show`: next, previous, a photo, play, pause,
  the interval, "do not show"; `POST /api/screens`: the code a TV shows, to pair it.
  The PC and the paired phones only; `GET /api/lan` (the address, the code and the QR
  code for the PC's page) the PC only.
- `GET /tv/<key>.jpg` (the TV's picture), `/thumb/<key>.jpg` and `/film/<key>.<ext>` (a
  video, 0292): the show's files only.

Nothing changes a photo: no route writes anything but the show held in memory.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan import PAIR_PREFIX
from media_hygiene.review.lan_app import LAN_PATH, lan_response
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.shared_routes import asset_or_page
from media_hygiene.review.videos import NEAR_POLICY
from media_hygiene.slideshow.door import Visitor, screen_cookie, screen_token
from media_hygiene.slideshow.pictures import slides_view
from media_hygiene.slideshow.screen_api import ScreenDesk, pair_screen

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.slideshow.desk import Desk
    from media_hygiene.slideshow.door import Door
    from media_hygiene.slideshow.pictures import ShowPictures

SCREEN_PATH: Final = "/screen"
SLIDES_PATH: Final = "/api/slides"
SHOW_PATH: Final = "/api/show"
SCREENS_PATH: Final = "/api/screens"
_GET, _POST = "GET", "POST"


@dataclass(frozen=True, slots=True)
class ShowPages:
    """The two pages: the remote (phone, PC) and the screen (TV)."""

    remote: bytes
    screen: bytes


@dataclass(frozen=True, slots=True)
class SlideshowApp:
    """Answers the TV, the phones and the PC."""

    desk: Desk
    door: Door
    pages: ShowPages
    pictures: ShowPictures

    async def handle(self, request: Request) -> Response:
        """Route a request by who sent it.

        Args:
            request: The request.

        Returns:
            The response.
        """
        visitor = self.door.visitor(request)
        if visitor is Visitor.OUTSIDER:
            message = _(
                "Open the slideshow at 127.0.0.1, or from the TV with mh --lan."
            )
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        if request.method == _GET and request.path == SCREEN_PATH:
            return self._screen_page(request, visitor)
        screen = ScreenDesk(self.desk, visitor, screen_token(request))
        answer = await screen.answer(request)
        if answer is not None:
            return answer
        if visitor is Visitor.PHONE:
            return await asset_or_page(self.door.local(request), self._remote)
        if visitor is Visitor.PC:
            local = request.path == LAN_PATH
            return self._lan() if local else await self._remote(request)
        return await self._stranger(request, visitor)

    def _lan(self) -> Response:
        """What the PC's remote shows to open the show elsewhere: `GET /api/lan`.

        Returns:
            The address, the code and the QR code; 404 without `mh --lan`.
        """
        if self.door.lan is None:
            return Response(HTTPStatus.NOT_FOUND)
        return lan_response(self.door.lan)

    async def _stranger(self, request: Request, visitor: Visitor) -> Response:
        """Answer a TV (its pictures) or a stranger (the pairing pages).

        Args:
            request: The request.
            visitor: A paired TV, or a stranger.

        Returns:
            The response.
        """
        if request.method != _GET:
            return self.door.stranger_page(request)
        if visitor is Visitor.SCREEN:
            pictured = await self.pictures.answer(request, tv_only=True)
            if pictured is not None:
                return pictured
        if request.path.startswith(PAIR_PREFIX):
            return self.door.pair_phone(request.path.removeprefix(PAIR_PREFIX))
        return self.door.stranger_page(request)

    def _screen_page(self, request: Request, visitor: Visitor) -> Response:
        """The TV's page; a TV not known yet gets a token in a cookie.

        Args:
            request: The request.
            visitor: Who sent it.

        Returns:
            The page.
        """
        headers: tuple[str, ...] = ()
        if visitor is Visitor.STRANGER:
            fresh = self.desk.screens.arrive(screen_token(request))
            if fresh is not None:
                headers = (screen_cookie(fresh),)
        return Response(
            HTTPStatus.OK,
            self.pages.screen,
            ContentType.HTML,
            policy=NEAR_POLICY,  # it plays the videos
            headers=headers,
        )

    async def _remote(self, request: Request) -> Response:
        """Answer the PC or a paired phone: the remote, the show, the pictures.

        Args:
            request: The request (a phone's names the loopback by now).

        Returns:
            The response.
        """
        if request.method == _POST:
            return self._posted(request)
        if request.method != _GET:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        path = request.path
        if path == PAGE_PATH:
            remote = self.pages.remote
            return Response(HTTPStatus.OK, remote, ContentType.HTML, policy=NEAR_POLICY)
        if path == SLIDES_PATH:
            return json_response(HTTPStatus.OK, slides_view(self.desk))
        if path.startswith(f"{SHOW_PATH}/"):
            since = path.removeprefix(f"{SHOW_PATH}/")
            await self.desk.settle(int(since) if since.isdigit() else 0)
            return json_response(HTTPStatus.OK, self.desk.state())
        pictured = await self.pictures.answer(request)
        return Response(HTTPStatus.NOT_FOUND) if pictured is None else pictured

    def _posted(self, request: Request) -> Response:
        """Answer an action of the remote, or the code of a TV typed on it.

        Args:
            request: The `POST`.

        Returns:
            The show as it now is, or why the request is refused.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        if request.path == SHOW_PATH:
            return self.desk.ask(request.body)
        if request.path == SCREENS_PATH:
            return pair_screen(self.desk, request.body)
        return Response(HTTPStatus.NOT_FOUND)
