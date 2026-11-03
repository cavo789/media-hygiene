"""What the window of `mh --lan` says (0269): the address and code for a phone.

The window of `mh` is minimised (0284): the PC's home page shows the same address, the
code and a QR code in its sidebar (`GET /api/lan`). An address refused (not one of a
home network) is said too: the page then stays on the PC only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.review.lan_address import lan_refused
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_phones import phone_book
from media_hygiene.review.local_app import PAGE_PATH

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.ending import Handling
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_page import AlbumPages


def say_lan(output: Output, lan: LanAccess | None) -> None:
    """Say how a phone opens the page, or why it cannot.

    Args:
        output: Where to say it.
        lan: The run's access; None without `mh --lan`, or with an address refused.
    """
    refused = lan_refused()
    if lan is None and refused is not None:
        output.warning(
            _(
                "{address} is not an address of a home network: the page stays on "
                "this PC only."
            ).format(address=refused)
        )
        return
    if lan is None:
        return
    output.info(
        _(
            "On a phone on the same Wi-Fi: open {url} and type the code {code} (or "
            "scan the QR code of the home page). Until mh stops; never the internet."
        ).format(url=f"{lan.origin}{PAGE_PATH}", code=lan.shown_code)
    )


def lan_door(
    runtime: Runtime, pages: AlbumPages, phone: tuple[LanAccess, bytes] | None
) -> Handling:
    """The albums' pages, behind the door of the home network under `mh --lan`.

    Args:
        runtime: Settings, mount points and output.
        pages: The albums' pages in front of the home page (their links too, 0462).
        phone: The run's access and the home page drawn for a phone; None without.

    Returns:
        What answers the requests.
    """
    if phone is None:
        return pages
    lan, page = phone
    return LanApp(  # phones paired for good under HTTPS (0431)
        pages,
        lan,
        page,
        phones=phone_book(secure=lan.secure),
        originals=runtime.settings.review.lan_phone_originals,
        links=pages.parts.links,  # one album by a 24 h link (0462)
    )
