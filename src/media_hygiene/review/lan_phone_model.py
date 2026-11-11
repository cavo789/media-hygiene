"""What `phones.json` / `tvs.json` keep of a paired device (0431, 0456, 0683).

Never its token, only the token's hash; since 0683 also when it was last seen and from
which address, and the name the user typed on the PC's card. Files written before 0683
load as they are: the new fields have defaults.
"""

from __future__ import annotations

import hashlib
from datetime import datetime  # pydantic reads the annotation at runtime
from typing import Final, Literal

from pydantic import BaseModel, ConfigDict

type Role = Literal["family", "guest"]
FAMILY: Final = "family"  # the whole library and the reports, as before 0684
GUEST: Final = "guest"  # the albums chosen for guests, nothing else (0684)


class Phone(BaseModel):
    """A paired device: never its token, only the token's hash."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    name: str
    paired: datetime
    digest: str
    last_seen: datetime | None = None  # at most once an hour (0683)
    address: str = ""  # its last address on the home network, from the socket
    role: Role = FAMILY  # 0684: a guest sees the albums chosen for guests only


class Phones(BaseModel):
    """The content of `phones.json`."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    phones: tuple[Phone, ...] = ()


def digest_of(token: str) -> str:
    """The hash kept for a token.

    Args:
        token: A phone's cookie.

    Returns:
        Its SHA-256, in hexadecimal.
    """
    return hashlib.sha256(token.encode()).hexdigest()


# The device named after the browser's own words, else a plain "phone".
_DEVICES: Final = (("iPhone", "iPhone"), ("iPad", "iPad"), ("Android", "Android"))
DEFAULT_DEVICE: Final = "Phone"


def device_name(user_agent: str) -> str:
    """Name a phone after its browser's `User-Agent`.

    Args:
        user_agent: The header.

    Returns:
        E.g. `Android`, `iPhone`; `DEFAULT_DEVICE` otherwise.
    """
    return next((name for word, name in _DEVICES if word in user_agent), DEFAULT_DEVICE)
