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

from media_hygiene.i18n import _
from media_hygiene.review.app_shell import shell_response
from media_hygiene.review.doors import Door
from media_hygiene.review.http import ContentType, Request, Response, is_local
from media_hygiene.review.lan import COOKIE_NAME, PAIR_PREFIX, cookies
from media_hygiene.review.lan_card import lan_response
from media_hygiene.review.lan_pairing import Pairing, pair_page
from media_hygiene.review.lan_paths import phone_may
from media_hygiene.review.lan_phones import device_name
from media_hygiene.review.lan_phones_api import (
    PHONE_PATHS,
    durable_cookie,
    phones_answer,
)
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response
from media_hygiene.review.shared_routes import asset_or_page
from media_hygiene.services.reviewing import HOST_LOOPBACK
from media_hygiene.share import album_page as albums

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.review.lan_phones import PhoneBook

LAN_PATH: Final = "/api/lan"
_GET = "GET"


@dataclass(frozen=True, slots=True)
class LanApp:
    """The home page, and what a phone paired on the home network may ask of it."""

    home: Handling
    lan: LanAccess
    phone_page: bytes  # the home page drawn for a phone: steps said to run on the PC
    pairing: Pairing = field(default_factory=Pairing)
    phones: PhoneBook | None = None  # under HTTPS: phones paired for good (0431)

    async def handle(self, request: Request) -> Response:
        """Let the loopback through; pair, filter and pass on a phone's requests.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if request.door is Door.PC:  # the loopback publish: refused there if not local
            return await self._pc(request)
        if not self.lan.names_me(request):  # whatever `Host` it forged (0384)
            return Response(HTTPStatus.FORBIDDEN)
        public = self._public(request)
        if public is not None:  # the pairing, the app's shell (0432)
            return public
        if not self._is_paired(request):
            if request.method == _GET:
                return pair_page(HTTPStatus.UNAUTHORIZED, closed=self.pairing.closed)
            return Response(HTTPStatus.FORBIDDEN)
        return await self._paired(request)

    async def _pc(self, request: Request) -> Response:
        """Answer the PC: the card, its paired phones, or the home page.

        Args:
            request: A request of the PC's door.

        Returns:
            The response.
        """
        if is_local(request) and request.path == LAN_PATH:
            return lan_response(self.lan, phones=self.phones is not None)
        if (
            is_local(request)
            and request.path in PHONE_PATHS
            and self.phones is not None
        ):
            return phones_answer(self.phones, request)
        return await self.home.handle(request)

    def _public(self, request: Request) -> Response | None:
        """Answer what needs no pairing: the code, the app's manifest, icons, worker.

        Args:
            request: A request of the home network's door.

        Returns:
            The response; None for anything else.
        """
        if request.method != _GET:
            return None
        if request.path.startswith(PAIR_PREFIX):
            return self._pair(request)
        return shell_response(request.path)  # nothing private

    def _pair(self, request: Request) -> Response:
        """Check the code; the right one pairs the phone, for good under HTTPS.

        Args:
            request: `GET /pair/<code>`.

        Returns:
            303 to the page with the cookie; the pairing page otherwise.
        """
        answer = self.pairing.check(self.lan, request.path.removeprefix(PAIR_PREFIX))
        if answer.status is not HTTPStatus.SEE_OTHER or self.phones is None:
            return answer
        token = self.phones.add(device_name(request.headers.get("user-agent", "")))
        if token is None:  # the file cannot be written: paired for this run only
            return answer
        headers = (f"Location: {PAGE_PATH}", durable_cookie(token))
        return Response(HTTPStatus.SEE_OTHER, headers=headers)

    def _is_paired(self, request: Request) -> bool:
        """Tell whether the phone holds this run's cookie, or one paired for good.

        Args:
            request: The request.

        Returns:
            True for a paired phone; a forgotten one is not.
        """
        if self.lan.is_paired(request):
            return True
        token = cookies(request.headers).get(COOKIE_NAME, "")
        return self.phones is not None and self.phones.knows(token)

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
