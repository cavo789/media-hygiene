"""The plain HTTP door beside the HTTPS one: the authority a phone installs (0430).

A phone that does not trust the PC's authority yet cannot open the HTTPS page. This
door, published on `LAN_CA_PORT`, serves only the steps to install it and `ca.crt`
(never `ca.key`); every other address goes on to the HTTPS page.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.lan_tls import CA_CERT

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request

CA_DOWNLOAD: Final = "/media-hygiene-ca.crt"
_STEPS_PATH: Final = "/"
_PACKAGE: Final = "media_hygiene.review"
_TEMPLATE: Final = "lan_ca.html.j2"


@dataclass(frozen=True, slots=True)
class CaDoor:
    """The steps, the authority, and the way on to the HTTPS page."""

    folder: Path  # the `/lan` folder
    secure_origin: str  # e.g. `https://192.168.1.20:8088`

    async def handle(self, request: Request) -> Response:
        """Answer a phone on the plain HTTP door.

        Args:
            request: The request.

        Returns:
            The steps, the authority, or 303 to the same address in HTTPS.
        """
        if request.method != "GET":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        if request.path == CA_DOWNLOAD:
            body = (self.folder / CA_CERT).read_bytes()
            return Response(HTTPStatus.OK, body, ContentType.CA_CERT)
        if request.path == _STEPS_PATH:
            return steps_page(self.secure_origin)
        location = f"Location: {self.secure_origin}{request.path}"
        return Response(HTTPStatus.SEE_OTHER, headers=(location,))


def steps_page(secure_origin: str) -> Response:
    """The steps to install the authority on Android and on an iPhone.

    Args:
        secure_origin: The HTTPS page to go on to once it is installed.

    Returns:
        The page.
    """
    template = translated_environment(_PACKAGE, escaped=("html", "j2")).get_template(
        _TEMPLATE
    )
    page = template.render(download=CA_DOWNLOAD, secure=f"{secure_origin}/")
    return Response(HTTPStatus.OK, page.encode(), ContentType.HTML)
