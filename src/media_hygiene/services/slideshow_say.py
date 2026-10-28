"""What the window of `slideshow` says: the TV's address, the phone's code.

Under `mh --lan` (0269): the address to type once in the TV's browser (then bookmark;
the plain HTTP door under HTTPS, a TV cannot trust the PC's authority),
and the phone's address and code. Without it, the show stays on this PC: the line
says how to open it to the TV. An address refused (not one of a home network) is said
as on the home page.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.review.doors import LAN_CA_PORT
from media_hygiene.review.lan_address import lan_refused
from media_hygiene.review.lan_ca_page import PHONE_STEPS
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.services.launcher_lan import LAN_FLAG
from media_hygiene.services.next_command import LAUNCHER_FUNCTION
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.slideshow.tv_door import SCREEN_PATH

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.review.lan import LanAccess
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.slideshow.door import Door


def announce_slideshow(runtime: Runtime, door: Door, port: int) -> None:
    """Say where the remote is, and how the TV and the phones open the show.

    Args:
        runtime: Settings, mount points and output.
        door: The run's access to the home network, if any.
        port: The port listened on, inside the container.
    """
    runtime.output.success(
        _(
            "Slideshow ready: the remote at {url} on this PC. Ctrl+C stops it; your "
            "photos are not changed."
        ).format(url=page_url(port))
    )
    address_tip(runtime.output, port)
    say_slideshow(runtime.output, door.lan)


def say_slideshow(output: Output, lan: LanAccess | None) -> None:
    """Tell the TV's and the phone's addresses, or how to get them.

    Args:
        output: The console of the run.
        lan: Under `mh --lan`, the address and the code; None otherwise.
    """
    if lan is not None:
        plain = f"http://{lan.address}:{LAN_CA_PORT}"
        screen = f"{plain}/" if lan.secure else f"{lan.origin}{SCREEN_PATH}"
        output.info(
            _(
                "On the TV, in its browser (the Chromecast's, or the TV's own): open "
                "{screen} once and bookmark it. It shows a code: type it on the "
                "phone's remote."
            ).format(screen=screen)
        )
        output.info(
            _(
                "On a phone on the same Wi-Fi: open {url} and type the code {code} "
                "(or scan the QR code of the PC's page). Until the slideshow stops; "
                "never the internet."
            ).format(url=f"{lan.origin}{PAGE_PATH}", code=lan.shown_code)
        )
        if lan.secure:  # HTTPS: a phone that never opened the home page trusts it first
            output.tip(
                _(
                    "A phone that says the connection is not private: install the "
                    "PC's certificate first, from {steps}. A phone paired on the home "
                    "page needs no code."
                ).format(steps=f"{plain}{PHONE_STEPS}")
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
