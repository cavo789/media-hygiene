"""The TV's door under HTTPS: the plain HTTP port beside the phone's (2026-10-28).

A TV cannot install the PC's authority (0430), and a phone that installed the app
must not meet the slideshow in plain HTTP (its app took the link over). So the phone's
remote is HTTPS, and the TV comes by the plain door (`LAN_CA_PORT`): its address `/`
leads to the screen page; then only what a TV asks (its code, the show, its pictures
and films). Nothing of the remote, no phone pairing: a phone there gets 404.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.videos import NEAR_POLICY
from media_hygiene.slideshow.door import Visitor, screen_cookie, screen_token
from media_hygiene.slideshow.screen_api import ScreenDesk

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.slideshow.app import SlideshowApp

SCREEN_PATH: Final = "/screen"
TV_HOME: Final = "/"
_GET: Final = "GET"


def screen_page(app: SlideshowApp, request: Request, visitor: Visitor) -> Response:
    """The TV's page; a TV not known yet gets a token in a cookie.

    Args:
        app: The slideshow.
        request: The request.
        visitor: Who sent it.

    Returns:
        The page.
    """
    headers: tuple[str, ...] = ()
    if visitor is Visitor.STRANGER:
        fresh = app.desk.screens.arrive(screen_token(request))
        if fresh is not None:
            headers = (screen_cookie(fresh),)
    return Response(
        HTTPStatus.OK,
        app.pages.screen,
        ContentType.HTML,
        policy=NEAR_POLICY,  # it plays the videos
        headers=headers,
    )


@dataclass(frozen=True, slots=True)
class TvDoor:
    """Answers the plain door: the TV's pages only."""

    app: SlideshowApp

    async def handle(self, request: Request) -> Response:
        """Answer a TV, or a stranger about to become one.

        Args:
            request: A request of the plain door (marked as the home network's).

        Returns:
            The screen page, the show, a picture; 403 or 404 for anything else.
        """
        app = self.app
        visitor = app.door.tv_visitor(request)
        if visitor is Visitor.OUTSIDER or request.method != _GET:
            return Response(HTTPStatus.FORBIDDEN)
        if request.path == TV_HOME:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {SCREEN_PATH}",))
        if request.path == SCREEN_PATH:
            return screen_page(app, request, visitor)
        screen = ScreenDesk(app.desk, visitor, screen_token(request))
        answer = await screen.answer(request)
        if answer is not None:
            return answer
        if visitor is Visitor.SCREEN:
            pictured = await app.pictures.answer(request, tv_only=True)
            if pictured is not None:
                return pictured
        return Response(HTTPStatus.NOT_FOUND)
