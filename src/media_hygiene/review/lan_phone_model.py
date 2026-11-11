"""What `phones.json` / `tvs.json` keep of a paired device (0431, 0456, 0683).

Never its token, only the token's hash; since 0683 also when it was last seen and from
which address, and the name the user typed on the PC's card. Files written before 0683
load as they are: the new fields have defaults.
"""

from __future__ import annotations

import hashlib
from datetime import datetime  # pydantic reads the annotation at runtime

from pydantic import BaseModel, ConfigDict


class Phone(BaseModel):
    """A paired device: never its token, only the token's hash."""

    model_config = ConfigDict(frozen=True, extra="ignore")

    id: str
    name: str
    paired: datetime
    digest: str
    last_seen: datetime | None = None  # at most once an hour (0683)
    address: str = ""  # its last address on the home network, from the socket


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
