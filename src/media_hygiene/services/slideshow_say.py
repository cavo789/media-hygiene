"""What the window of `slideshow` says: the TV's address, the phone's code.

Under `mh --lan` (0269): the address to type once in the TV's browser (then bookmark),
and the phone's address and code. Without it, the show stays on this PC: the line
says how to open it to the TV. An address refused (not one of a home network) is said
as on the home page.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.review.lan import lan_refused
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.services.launcher_lan import LAN_FLAG
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.slideshow.app import SCREEN_PATH

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.lan import LanAccess


def say_slideshow(output: Output, lan: LanAccess | None) -> None:
    """Tell the TV's and the phone's addresses, or how to get them.

    Args:
        output: The console of the run.
        lan: Under `mh --lan`, the address and the code; None otherwise.
    """
    if lan is not None:
        output.info(
            _(
                "On the TV, in its browser (the Chromecast's, or the TV's own): open "
                "{screen} once and bookmark it. It shows a code: type it on the "
                "phone's remote."
            ).format(screen=f"{lan.origin}{SCREEN_PATH}")
        )
        output.info(
            _(
                "On a phone on the same Wi-Fi: open {url} and type the code {code} "
                "(or scan the QR code of the PC's page). Until the slideshow stops; "
                "never the internet."
            ).format(url=f"{lan.origin}{PAGE_PATH}", code=lan.shown_code)
        )
        return
    given = lan_refused()
    if given is None:
        output.tip(
            _(
                "For the TV and your phone: {command} (Windows PowerShell). The show "
                "then opens to the home network, never to the internet."
            ).format(command=f"{LAUNCHER_FUNCTION} slideshow {LAN_FLAG} …")
        )
        return
    message = _(
        "{address} is not an address of a home network: the slideshow stays on this "
        "PC only."
    )
    output.warning(message.format(address=given))
