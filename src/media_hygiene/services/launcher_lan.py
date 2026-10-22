r"""What `mh --lan` needs: its variables, the addresses it takes, its messages (0269).

`mh --lan` (PowerShell) runs the home page as `mh` alone does, its port published on the
PC's address on the home network too: a private IPv4 address of the adapter reaching
the router (`Get-NetIPConfiguration`), never every interface, never a public address.
It draws a secret for the run (`RandomNumberGenerator`, no `Add-Type`: 0257) from which
the page derives the pairing code and the phone's token (`review/lan.py`). Windows may
ask whether Docker Desktop may accept connections: on a private network only. The bash
`mh` refuses it: Docker under WSL publishes on Windows' own loopback.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import Final

from media_hygiene.i18n import _
from media_hygiene.review.lan import LAN_ADDRESS_VARIABLE, LAN_SECRET_VARIABLE
from media_hygiene.services.launcher_phone_say import say
from media_hygiene.services.next_command import LAUNCHER_FUNCTION

LAN_FLAG: Final = "--lan"
# The commands whose page `--lan` opens to the home network: the home page (0269), the
# slideshow (0291, `mh slideshow --lan`, or chosen on a home page opened by `mh --lan`).
LAN_SHOWS: Final = ("slideshow",)
SECRET_BYTES: Final = 32
# The private IPv4 ranges (RFC 1918), for PowerShell's -match: a home network only.
PRIVATE_IPV4: Final = r"^(10\.|192\.168\.|172\.(1[6-9]|2[0-9]|3[01])\.)"
# The network category Windows' firewall treats as untrusted (Get-NetConnectionProfile).
PUBLIC_CATEGORY: Final = "Public"


@dataclass(frozen=True, slots=True)
class LanTexts:
    """The messages of `mh --lan`, ready to sit inside double quotes."""

    none: str  # no private address found
    opening: str  # holds `${address}`
    firewall: str  # Windows may ask about Docker Desktop
    public: str  # the network is "Public" for Windows
    windows: str  # the bash `mh`: PowerShell only


@dataclass(frozen=True, slots=True)
class LanCommand:  # pylint: disable=too-many-instance-attributes  # one per template value
    """What the scripts need to run, or refuse, `mh --lan`."""

    flag: str
    shows: tuple[str, ...]  # `mh <command> --lan`; their page and home's published
    address: str  # the variable naming the PC's address
    secret: str  # the variable holding the run's secret
    secret_bytes: int
    private: str
    public: str
    texts: LanTexts


def lan_command() -> LanCommand:
    """Gather what `mh --lan` needs, its messages translated.

    Returns:
        The variables, the patterns and the messages.
    """
    command = f"{LAUNCHER_FUNCTION} {LAN_FLAG}"
    return LanCommand(
        flag=LAN_FLAG,
        shows=LAN_SHOWS,
        address=LAN_ADDRESS_VARIABLE,
        secret=LAN_SECRET_VARIABLE,
        secret_bytes=SECRET_BYTES,
        private=PRIVATE_IPV4,
        public=PUBLIC_CATEGORY,
        texts=LanTexts(
            none=say(
                _(
                    "{command}: this PC has no address on a home network (Wi-Fi or "
                    "cable to a router): the page stays on this PC."
                ).replace("{command}", command)
            ),
            opening=say(
                _(
                    "The home page opens to the phones of the home network too, at "
                    "{address}, until mh stops. Never the internet."
                ),
                "address",
            ),
            firewall=say(
                _(
                    "Windows may ask whether Docker Desktop may accept connections: "
                    "allow it on private networks only."
                )
            ),
            public=say(
                _(
                    "Windows counts this network as public: its firewall blocks the "
                    "phone. On a home network, set it to private in Windows' Settings "
                    "(Network and Internet)."
                )
            ),
            windows=say(
                _("{command} works in Windows PowerShell only, for now.").replace(
                    "{command}", command
                )
            ),
        ),
    )
