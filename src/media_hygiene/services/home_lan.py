"""What the window of `mh --lan` says (0269): the address and code for a phone.

The window of `mh` is minimised (0284): the PC's home page shows the same address, the
code and a QR code in its sidebar (`GET /api/lan`). An address refused (not one of a
home network) is said too: the page then stays on the PC only.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.review.lan_address import lan_refused
from media_hygiene.review.local_app import PAGE_PATH

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.lan import LanAccess


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
