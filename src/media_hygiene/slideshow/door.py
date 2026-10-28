"""Who asks the slideshow's server: the PC, a phone, a TV, or nobody it knows.

The PC (a loopback `Host`) may do everything, as on every page. Under `mh --lan`, a
request naming the PC's address on the home network, exactly (`LanAccess.names_me`:
another name is DNS rebinding), is a phone paired by the run's code (0269's cookie,
`/pair/<code>` as on the home page), a TV paired by its own code (`screens`), or a
stranger: a stranger sees the screen page with its code, or the phone's pairing page,
nothing else. A phone paired for good (`phones.json`, 0431), here or on the home page,
needs no code. Under HTTPS the TV comes by the plain door (`tv_door`): only a TV or a
stranger there, never a phone. Any other `Host` is refused. Never the internet:
`mh --lan` publishes the port on the PC's private address only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from enum import Enum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.doors import LAN_CA_PORT
from media_hygiene.review.http import Request, Response, is_local
from media_hygiene.review.lan import COOKIE_NAME, PAIR_PREFIX, cookies
from media_hygiene.review.lan_pairing import Pairing, pair_page
from media_hygiene.review.lan_phones_api import for_good
from media_hygiene.services.reviewing import HOST_LOOPBACK
from media_hygiene.slideshow.screens import SCREEN_COOKIE

if TYPE_CHECKING:
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.review.lan_phones import PhoneBook
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
    phones: PhoneBook | None = None  # under HTTPS: phones paired for good (0431)

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
        if self._is_phone(request):
            return Visitor.PHONE
        return self._screen(request)

    def tv_visitor(self, request: Request) -> Visitor:
        """Tell who came by the plain door: a TV paired, a stranger, or an outsider.

        Args:
            request: A request of the plain HTTP door (HTTPS for the phones only).

        Returns:
            Never a phone, nor the PC: that door serves the TV's pages only.
        """
        named = f"{self.lan.address}:{LAN_CA_PORT}" if self.lan else None
        if named is None or request.headers.get("host", "") != named:
            return Visitor.OUTSIDER
        return self._screen(request)

    def _screen(self, request: Request) -> Visitor:
        """A TV paired by its code, or a stranger.

        Args:
            request: The request.

        Returns:
            The visitor.
        """
        if self.screens.is_paired(screen_token(request)):
            return Visitor.SCREEN
        return Visitor.STRANGER

    def _is_phone(self, request: Request) -> bool:
        """Tell whether a phone holds this run's cookie, or one paired for good.

        Args:
            request: The request.

        Returns:
            True for a paired phone; a phone forgotten on the PC's page is not.
        """
        if self.lan is not None and self.lan.is_paired(request):
            return True
        token = cookies(request.headers).get(COOKIE_NAME, "")
        return self.phones is not None and self.phones.knows(token)

    def pair_phone(self, request: Request) -> Response:
        """Check the run's code typed on a phone; the right one opens the remote.

        Args:
            request: `GET /pair/<code>`.

        Returns:
            303 to the remote with the phone's cookie, for good under HTTPS as on
            the home page (0431); the pairing page otherwise.
        """
        if self.lan is None:
            return Response(HTTPStatus.FORBIDDEN)
        typed = request.path.removeprefix(PAIR_PREFIX)
        return for_good(self.pairing.check(self.lan, typed), self.phones, request)

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
