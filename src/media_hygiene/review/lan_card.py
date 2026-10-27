"""What the PC's page shows to pair a phone: the address, the code, the QR code (0269).

Under HTTPS, where a phone installs the PC's authority first (0430), and the paths of
the phones paired for good (0431).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import segno

from media_hygiene.review.doors import LAN_CA_PORT
from media_hygiene.review.lan_phones_api import FORGET_PATH, PHONES_PATH
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from media_hygiene.review.http import Response
    from media_hygiene.review.lan import LanAccess

_QR_SCALE: Final = 5
_QR_BORDER: Final = 2


def lan_response(lan: LanAccess, *, phones: bool = False) -> Response:
    """What the PC's page shows to pair a phone: the address, the code, the QR code.

    Args:
        lan: The run's access.
        phones: Phones are paired for good: where the page lists and forgets them.

    Returns:
        JSON: `url`, `code`, `qr` (an SVG drawing of the pairing address), under
        HTTPS `ca`: where a phone installs the PC's authority first (0430), and with
        `phones`, the paths `phones` and `forget` (0431).
    """
    qr = segno.make(lan.pair_url, error="m").svg_inline(
        scale=_QR_SCALE, border=_QR_BORDER, dark="#000", light="#fff"
    )
    url = f"{lan.origin}{PAGE_PATH}"
    card: dict[str, object] = {"url": url, "code": lan.shown_code, "qr": qr}
    if lan.secure:
        card["ca"] = f"http://{lan.address}:{LAN_CA_PORT}/"
    if phones:
        card |= {"phones": PHONES_PATH, "forget": FORGET_PATH}
    return json_response(HTTPStatus.OK, card)
