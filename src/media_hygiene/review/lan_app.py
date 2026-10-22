"""The home page's door to the home network: pairing, then what a phone may do (0269).

In front of the home page under `mh --lan`. A request from the loopback goes through
as before, plus `GET /api/lan` (the address, the code and its QR code for the PC's
page; never to the network). A request naming the PC's address on the home network:

- `GET /pair/<code>`: the right code sets the phone's cookie and opens the home page;
  `MAX_FAILURES` wrong ones close the pairing until the server stops;
- without the cookie, every `GET` gets the pairing page, anything else 403;
- with it, only the reads (`READ_PATHS`, `READ_PREFIXES`: the page, its state, the
  reports, the theme, the docs, the albums and their files, 0297), the audit of the
  page (`POST /api/audit`) and a change of an album (`POST /api/albums`, 0295): none
  changes a photo. A step, Quit or the presence stay the PC's: 403, said on each
  step's button (decided 2026-10-21). What passes is handed on as from the loopback,
  its `Origin` checked; any other `Host` (DNS rebinding) is refused as before.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import segno

from media_hygiene.docs.pages import DOCS_PREFIX
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.home_app import AUDIT_PATH
from media_hygiene.review.home_assets import ASSETS_PREFIX, FAVICON_PATH
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.http import ContentType, Request, Response, is_local
from media_hygiene.review.lan import CODE_DIGITS, COOKIE_NAME, PAIR_PREFIX
from media_hygiene.review.local_app import PAGE_PATH, STATE_PATH
from media_hygiene.review.serving import json_response
from media_hygiene.review.shared_routes import asset_or_page
from media_hygiene.services.reviewing import HOST_LOOPBACK
from media_hygiene.share import album_page as albums

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.lan import LanAccess

LAN_PATH: Final = "/api/lan"
MAX_FAILURES: Final = 5  # wrong codes before the pairing closes for this server
_HOME_READS: Final = frozenset({PAGE_PATH, STATE_PATH, AUDIT_PATH, FAVICON_PATH})
READ_PATHS: Final = _HOME_READS | albums.PHONE_READS
_HOME_PREFIXES: Final = (REPORTS_PREFIX, ASSETS_PREFIX, DOCS_PREFIX)
READ_PREFIXES: Final = (*_HOME_PREFIXES, *albums.PHONE_READ_PREFIXES)
WRITE_PATHS: Final = albums.PHONE_WRITES | {AUDIT_PATH}
_GET, _POST = "GET", "POST"
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
        cookie = f"{COOKIE_NAME}={lan.token}; Path=/; HttpOnly; SameSite=Lax"
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
        if is_local(request) and request.path == LAN_PATH:
            return lan_response(self.lan)
        if is_local(request) or not self.lan.names_me(request):
            return await self.home.handle(request)  # another host: refused there
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
        reads = request.method == _GET and (
            path in READ_PATHS or path.startswith(READ_PREFIXES)
        )
        writes = request.method == _POST and path in WRITE_PATHS
        origin = request.headers.get("origin")
        if not (reads or writes) or origin not in {None, self.lan.origin}:
            message = _(
                "From the phone: the audit, the reports and the albums. Run this "
                "step on the PC."
            )
            return json_response(HTTPStatus.FORBIDDEN, {"error": message})
        if request.method == _GET and path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.phone_page, ContentType.HTML)
        local = f"{HOST_LOOPBACK}:{self.lan.port}"
        headers = {**request.headers, "host": local}
        if origin is not None:
            headers["origin"] = f"http://{local}"
        passed = Request(request.method, path, headers, request.body)
        return await asset_or_page(passed, self.home.handle)


def lan_response(lan: LanAccess) -> Response:
    """What the PC's page shows to pair a phone: the address, the code, the QR code.

    Args:
        lan: The run's access.

    Returns:
        JSON: `url`, `code`, and `qr` (an SVG drawing of the pairing address).
    """
    qr = segno.make(lan.pair_url, error="m").svg_inline(
        scale=_QR_SCALE, border=_QR_BORDER, dark="#000", light="#fff"
    )
    url = f"{lan.origin}{PAGE_PATH}"
    return json_response(HTTPStatus.OK, {"url": url, "code": lan.shown_code, "qr": qr})


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
