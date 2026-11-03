"""One album opened by a link for 24 h, without pairing (0462, design of 0334).

Per album a random token (192 bits), kept **in memory** by this run of `mh --lan`:
never written to disk, so a restart of `mh` revokes every link; *Stop sharing* drops
one at once. A token is compared in constant time; unknown and expired answer alike.
"""

from __future__ import annotations

import hmac
import secrets
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.share.albums import same_name

if TYPE_CHECKING:
    from collections.abc import Callable

# How long a link opens its album (decided 2026-10-27; a setting only if asked).
LINK_HOURS: Final = 24
_SECONDS_PER_HOUR: Final = 3600
_TOKEN_BYTES: Final = 24  # 192 bits


@dataclass(frozen=True, slots=True)
class AlbumLink:
    """A link: its token, the album it opens, until when (the clock's seconds)."""

    token: str
    name: str
    until: float


class AlbumLinks:
    """The links of this run: token → album, each for `LINK_HOURS`."""

    __slots__ = ("_links", "_now")

    def __init__(self, now: Callable[[], float] = time.monotonic) -> None:
        """Start without any link.

        Args:
            now: The clock, in seconds (a test's own).
        """
        self._links: list[AlbumLink] = []
        self._now = now

    def make(self, name: str) -> AlbumLink:
        """A new link to an album; its earlier one stops working.

        Args:
            name: The album, as saved.

        Returns:
            The link.
        """
        self.stop(name)
        until = self._now() + LINK_HOURS * _SECONDS_PER_HOUR
        link = AlbumLink(secrets.token_urlsafe(_TOKEN_BYTES), name, until)
        self._links.append(link)
        return link

    def stop(self, name: str) -> bool:
        """*Stop sharing*: the album's link opens nothing from now on.

        Args:
            name: The album, whatever its case.

        Returns:
            True when a link was dropped.
        """
        before = len(self._links)
        self._links = [k for k in self._links if same_name(k.name) != same_name(name)]
        return len(self._links) != before

    def shared(self, name: str) -> AlbumLink | None:
        """The album's link still working, if any.

        Args:
            name: The album, whatever its case.

        Returns:
            It, or None.
        """
        self._forget_expired()
        wanted = same_name(name)
        return next((k for k in self._links if same_name(k.name) == wanted), None)

    def opened(self, token: str) -> str | None:
        """The album a token opens: compared in constant time, expired ones forgotten.

        Args:
            token: As the address holds it.

        Returns:
            The album's name; None for an unknown, expired or stopped token.
        """
        self._forget_expired()
        asked = token.encode()
        found = None
        for link in self._links:  # every one compared: no early answer to time
            if hmac.compare_digest(link.token.encode(), asked):
                found = link.name
        return found

    def _forget_expired(self) -> None:
        """Drop the links whose 24 h are over."""
        now = self._now()
        self._links = [link for link in self._links if link.until > now]
