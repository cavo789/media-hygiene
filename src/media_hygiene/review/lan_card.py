"""What the PC's page shows to pair a phone: the address, the code, the QR code (0269).

Under HTTPS, where a phone installs the PC's authority first (0430), and the paths of
the phones paired for good (0431).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import segno

from media_hygiene.cli.menu_entry import Doc
from media_hygiene.docs.served import served_url
from media_hygiene.review.doors import LAN_CA_PORT
from media_hygiene.review.lan_ca_page import PHONE_STEPS
from media_hygiene.review.lan_phones_api import FORGET_PATH, PHONES_PATH
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.serving import json_response

if TYPE_CHECKING:
    from media_hygiene.review.http import Response
    from media_hygiene.review.lan import LanAccess

_QR_SCALE: Final = 5
TV_SCREEN: Final = "/screen"  # the TV's page on the plain door (`slideshow/tv_door`)
_QR_BORDER: Final = 2
# The steps to install the certificate on each phone, in the docs (0430).
CA_DOC: Final = Doc(
    "commands/home/",
    "#once-per-phone-install-the-certificate",
    "#une-fois-par-téléphone--installer-le-certificat",
)


def lan_response(lan: LanAccess, *, phones: bool = False, tv: bool = False) -> Response:
    """What the PC's page shows to pair a phone: the address, the code, the QR code.

    Args:
        lan: The run's access.
        phones: Phones are paired for good: where the page lists and forgets them.
        tv: The slideshow's: under HTTPS, the TV's address on the plain door.

    Returns:
        JSON: `url`, `code`, `qr` (an SVG drawing of the pairing address), under
        HTTPS `ca`: where a phone installs the PC's authority first (0430), and with
        `phones`, the paths `phones` and `forget` (0431); with `tv` under HTTPS, `tv`.
    """
    qr = segno.make(lan.pair_url, error="m").svg_inline(
        scale=_QR_SCALE, border=_QR_BORDER, dark="#000", light="#fff"
    )
    url = f"{lan.origin}{PAGE_PATH}"
    card: dict[str, object] = {"url": url, "code": lan.shown_code, "qr": qr}
    if lan.secure:
        plain = f"http://{lan.address}:{LAN_CA_PORT}"
        card["ca"] = f"{plain}{PHONE_STEPS if tv else '/'}"
        if tv:
            card["tv"] = f"{plain}{TV_SCREEN}"  # the same in the home server (0417)
        card["caHelp"] = served_url(CA_DOC)
    if phones:
        card |= {"phones": PHONES_PATH, "forget": FORGET_PATH}
    return json_response(HTTPStatus.OK, card)
