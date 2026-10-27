"""The PC's address on the home network `mh --lan` gives, when private (0269).

Only a private IPv4 address is taken: never the internet.
"""

from __future__ import annotations

import ipaddress
import os
from typing import Final

from media_hygiene.services.next_command import LAUNCHER_VARIABLE

LAN_ADDRESS_VARIABLE: Final = f"{LAUNCHER_VARIABLE}_LAN_ADDRESS"


def private_address(text: str) -> str | None:
    """Accept an address of a home network only: a private IPv4, never the internet.

    Args:
        text: The address `mh` found.

    Returns:
        It, or None for a public, loopback, link-local or malformed address.
    """
    try:
        address = ipaddress.IPv4Address(text.strip())
    except ValueError:
        return None
    if not address.is_private or address.is_loopback or address.is_link_local:
        return None
    return str(address)


def lan_address() -> str | None:
    """The address `mh --lan` gave, when it is one of a home network.

    Returns:
        It, or None without `mh --lan` or with an address refused.
    """
    return private_address(os.environ.get(LAN_ADDRESS_VARIABLE, ""))


def lan_refused() -> str | None:
    """The address `mh --lan` gave when it is refused, to say so.

    Returns:
        The address given, or None when none was given or it was accepted.
    """
    given = os.environ.get(LAN_ADDRESS_VARIABLE, "").strip()
    if not given or private_address(given) is not None:
        return None
    return given
