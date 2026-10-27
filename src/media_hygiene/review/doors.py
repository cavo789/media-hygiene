"""The door a request came in by: the PC's or the home network's (0384).

Under `mh --lan` the container listens on two ports: the usual one, published on the
PC's loopback only, and `LAN_DOOR_PORT`, published on the PC's address on the home
network. A request is told apart by the socket it arrived on, never by a header the
client writes (`Host` can be forged): only the PC's door may pass for the PC.
"""

from __future__ import annotations

import os
from enum import StrEnum
from typing import Final

from media_hygiene.constants import ENV_PREFIX

# Set by `mh --lan` (`-e`): the container port its home network publish reaches.
LAN_DOOR_VARIABLE: Final = f"{ENV_PREFIX}LAUNCHER_LAN_DOOR"
# Inside the container only: never the page's own port (a free one, any machine).
LAN_DOOR_PORT: Final = 48088
# Plain HTTP beside the HTTPS door: the authority a phone installs, once (0430).
LAN_CA_DOOR_PORT: Final = 48089
# Published on the PC's address: the page's port + 1 (a setting only if it collides).
LAN_CA_PORT: Final = 8089


class Door(StrEnum):
    """The listening socket a request came in by."""

    PC = "pc"  # the loopback publish: the PC itself
    LAN = "lan"  # the home network publish: a phone, a TV, any device of the Wi-Fi


def lan_door_port() -> int | None:
    """The container port of the home network's door, when `mh --lan` opened one.

    Returns:
        The port, or None without `mh --lan` (or a value that is not a port).
    """
    given = os.environ.get(LAN_DOOR_VARIABLE, "").strip()
    return int(given) if given.isdigit() else None
