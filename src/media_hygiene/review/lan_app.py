"""The home page's door to the home network: pairing, then what a phone may do (0269).

In front of the home page under `mh --lan`. A request of the PC's door goes through as
before, plus `GET /api/lan` (the code and its QR code for the PC's page). A request of
the home network's door (`doors`, 0384: never passed on as the PC's, whatever its
`Host`) must name the PC's address on the home network, then:

- `GET /pair/<code>`: the right code sets the phone's cookie and opens the home page;
  `MAX_FAILURES` wrong ones close the pairing until the server stops;
- without the cookie, every `GET` gets the pairing page, anything else 403;
- with it, only what `lan_paths` lists: the reads (the page, its state, the reports,
  the theme, the docs, the albums, search and browse and their files, 0297, 0360), the
  audit, a search or a folder listed, and a change of an album (0295): none changes a
  photo. A step or a stop stay the PC's: 403, said on each
  step's button (decided 2026-10-21). What passes goes on as the PC's, `Origin` checked.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import segno

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.doors import LAN_CA_PORT, Door
from media_hygiene.review.http import ContentType, Request, Response, is_local
from media_hygiene.review.lan import CODE_DIGITS, COOKIE_NAME, PAIR_PREFIX
from media_hygiene.review.lan_paths import phone_may
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response
from media_hygiene.review.shared_routes import asset_or_page
from media_hygiene.services.reviewing import HOST_LOOPBACK
from media_hygiene.share import album_page as albums

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.lan import LanAccess

LAN_PATH: Final = "/api/lan"
MAX_FAILURES: Final = 5  # wrong codes before the pairing closes for this server
_GET = "GET"
_QR_SCALE: Final = 5
_QR_BORDER: Final = 2
_PACKAGE: Final = "media_hygiene.review"
_PAIR_TEMPLATE: Final = "lan_pair.html.j2"


class Pairing:
    """The wrong codes typed so far, for this server."""

    __slots__ = ("failures",)

    def __init__(self) -> None:
        """Start without any wrong code."""
        self.failures = 0

    @property
    def closed(self) -> bool:
        """Tell whether too many wrong codes were typed.

        Returns:
            True from `MAX_FAILURES` on.
        """
        return self.failures >= MAX_FAILURES

    def check(self, lan: LanAccess, typed: str) -> Response:
        """Check a code; the right one sets the phone's cookie and opens `/`.

        Args:
            lan: The run's access.
            typed: The code, from the path.

        Returns:
            303 to `/` with the cookie; the pairing page again otherwise.
        """
        if self.closed:
            return pair_page(HTTPStatus.TOO_MANY_REQUESTS, closed=True)
        if not lan.code_matches(typed):
            self.failures += 1
            return pair_page(HTTPStatus.FORBIDDEN, closed=self.closed)
        secure = "; Secure" if lan.secure else ""  # HTTPS (0430)
        cookie = f"{COOKIE_NAME}={lan.token}; Path=/; HttpOnly; SameSite=Lax{secure}"
        headers = (f"Location: {PAGE_PATH}", f"Set-Cookie: {cookie}")
        return Response(HTTPStatus.SEE_OTHER, headers=headers)


@dataclass(frozen=True, slots=True)
class LanApp:
    """The home page, and what a phone paired on the home network may ask of it."""

    home: Handling
    lan: LanAccess
    phone_page: bytes  # the home page drawn for a phone: steps said to run on the PC
    pairing: Pairing = field(default_factory=Pairing)

    async def handle(self, request: Request) -> Response:
        """Let the loopback through; pair, filter and pass on a phone's requests.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.door is Door.PC:  # the loopback publish: refused there if not local
            card = is_local(request) and request.path == LAN_PATH
            return lan_response(self.lan) if card else await self.home.handle(request)
        if not self.lan.names_me(request):  # whatever `Host` it forged (0384)
            return Response(HTTPStatus.FORBIDDEN)
        if request.path.startswith(PAIR_PREFIX) and request.method == _GET:
            return self.pairing.check(self.lan, request.path.removeprefix(PAIR_PREFIX))
        if not self.lan.is_paired(request):
            if request.method == _GET:
                return pair_page(HTTPStatus.UNAUTHORIZED, closed=self.pairing.closed)
            return Response(HTTPStatus.FORBIDDEN)
        return await self._paired(request)

    async def _paired(self, request: Request) -> Response:
        """Answer a paired phone: the reads, the audit, the albums, as from the PC.

        Args:
            request: The request.

        Returns:
            The response; 403 for a step, Quit, or another site's request.
        """
        path = request.path
        origin = request.headers.get("origin")
        if not phone_may(request) or origin not in {None, self.lan.origin}:
            message = _(
                "From the phone: the audit, the reports, the albums, the search and "
                "browse. Open this page or run this step on the PC."
            )
            return json_response(HTTPStatus.FORBIDDEN, {"error": message})
        if request.method == _GET and path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.phone_page, ContentType.HTML)
        local = f"{HOST_LOOPBACK}:{self.lan.port}"
        headers = {**request.headers, "host": local, albums.PHONE_HEADER: "1"}
        if origin is not None:
            headers["origin"] = f"http://{local}"
        passed = Request(request.method, path, headers, request.body)
        return await asset_or_page(passed, self.home.handle)


def lan_response(lan: LanAccess) -> Response:
    """What the PC's page shows to pair a phone: the address, the code, the QR code.

    Args:
        lan: The run's access.

    Returns:
        JSON: `url`, `code`, `qr` (an SVG drawing of the pairing address), and under
        HTTPS `ca`: where a phone installs the PC's authority first (0430).
    """
    qr = segno.make(lan.pair_url, error="m").svg_inline(
        scale=_QR_SCALE, border=_QR_BORDER, dark="#000", light="#fff"
    )
    url = f"{lan.origin}{PAGE_PATH}"
    card: dict[str, object] = {"url": url, "code": lan.shown_code, "qr": qr}
    if lan.secure:
        card["ca"] = f"http://{lan.address}:{LAN_CA_PORT}/"
    return json_response(HTTPStatus.OK, card)


def pair_page(status: HTTPStatus, *, closed: bool) -> Response:
    """The pairing page, and why the last code was refused.

    Args:
        status: 401 before any code, 403 after a wrong one, 429 once closed.
        closed: Too many wrong codes: no form any more.

    Returns:
        The page.
    """
    problem = ""
    if closed:
        problem = _(
            "Too many wrong codes: pairing is closed. On the PC, quit Media Hygiene, "
            "then type mh --lan again for a new code."
        )
    elif status is HTTPStatus.FORBIDDEN:
        problem = _("This is not the code shown on the PC: type it again.")
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _PAIR_TEMPLATE
    )
    page = template.render(
        problem=problem, closed=closed, digits=CODE_DIGITS, prefix=PAIR_PREFIX
    )
    return Response(status, page.encode(), ContentType.HTML)
