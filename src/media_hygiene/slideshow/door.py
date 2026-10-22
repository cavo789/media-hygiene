"""Who asks the slideshow's server: the PC, a phone, a TV, or nobody it knows.

The PC (a loopback `Host`) may do everything, as on every page. Under `mh --lan`, a
request naming the PC's address on the home network, exactly (`LanAccess.names_me`:
another name is DNS rebinding), is a phone paired by the run's code (0269's cookie,
`/pair/<code>` as on the home page), a TV paired by its own code (`screens`), or a
stranger: a stranger sees the screen page with its code, or the phone's pairing page,
nothing else. Any other `Host` is refused. Never the internet: `mh --lan` publishes
the port on the PC's private address only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Request, Response, is_local
from media_hygiene.review.lan import cookies
from media_hygiene.review.lan_app import Pairing, pair_page
from media_hygiene.services.reviewing import HOST_LOOPBACK
from media_hygiene.slideshow.screens import SCREEN_COOKIE

if TYPE_CHECKING:
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.slideshow.screens import Screens

# Kept by the TV across its browser's restarts while the server runs.
_SCREEN_AGE_SECONDS: Final = 24 * 3600


class Visitor(Enum):
    """Who sent a request."""

    PC = "pc"  # the loopback
    PHONE = "phone"  # paired by the run's code
    SCREEN = "screen"  # a TV paired by its own code
    STRANGER = "stranger"  # the PC's LAN address, not paired
    OUTSIDER = "outsider"  # another host: refused


@dataclass(frozen=True, slots=True)
class Door:
    """The run's access to the home network (None without `mh --lan`), and the TVs."""

    lan: LanAccess | None
    screens: Screens
    pairing: Pairing = field(default_factory=Pairing)

    def visitor(self, request: Request) -> Visitor:
        """Tell who sent a request.

        Args:
            request: The request.

        Returns:
            The visitor.
        """
        if is_local(request):
            return Visitor.PC
        if self.lan is None or not self.lan.names_me(request):
            return Visitor.OUTSIDER
        if self.lan.is_paired(request):
            return Visitor.PHONE
        if self.screens.is_paired(screen_token(request)):
            return Visitor.SCREEN
        return Visitor.STRANGER

    def pair_phone(self, typed: str) -> Response:
        """Check the run's code typed on a phone; the right one opens the remote.

        Args:
            typed: The code, from the path.

        Returns:
            303 to the remote with the phone's cookie; the pairing page otherwise.
        """
        if self.lan is None:
            return Response(HTTPStatus.FORBIDDEN)
        return self.pairing.check(self.lan, typed)

    def stranger_page(self, request: Request) -> Response:
        """What a stranger gets: the pairing page for a `GET`, 403 otherwise.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.method != "GET":
            return Response(HTTPStatus.FORBIDDEN)
        return pair_page(HTTPStatus.UNAUTHORIZED, closed=self.pairing.closed)

    def local(self, request: Request) -> Request:
        """A phone's request as if from the loopback: the remote, the theme, the docs.

        Its `Origin`, when it is the remote's own address, is the loopback's too;
        another site's stays, and its `POST` is refused.

        Args:
            request: The phone's request.

        Returns:
            The same request naming the loopback.
        """
        port = 0 if self.lan is None else self.lan.port
        local = f"{HOST_LOOPBACK}:{port}"
        headers = {**request.headers, "host": local}
        origin = request.headers.get("origin")
        if self.lan is not None and origin == self.lan.origin:
            headers["origin"] = f"http://{local}"  # the remote's own: a POST passes
        return Request(request.method, request.path, headers, request.body)


def screen_token(request: Request) -> str:
    """The TV's token, from its cookie.

    Args:
        request: The request.

    Returns:
        It; empty without one.
    """
    return cookies(request.headers).get(SCREEN_COOKIE, "")


def screen_cookie(token: str) -> str:
    """The header that gives a TV its token.

    Args:
        token: The token drawn for it.

    Returns:
        The `Set-Cookie` header line.
    """
    return (
        f"Set-Cookie: {SCREEN_COOKIE}={token}; Path=/; HttpOnly; SameSite=Lax; "
        f"Max-Age={_SCREEN_AGE_SECONDS}"
    )
