"""The wrong pairing codes, counted per device address and kept for the PC (0681).

One device that types wrong codes waits, never the others: after `FREE_TRIES` wrong
codes from one address, that address waits `FIRST_WAIT` seconds, doubling at each new
wrong code, up to `LONGEST_WAIT`. A ceiling for the whole run (`MAX_FAILURES`) still
closes the pairing, until the PC's page opens it again. Constants, not settings: no
collection changes how many guesses a stranger deserves.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, replace
from typing import Final

FREE_TRIES: Final = 3  # wrong codes of one address before it waits
FIRST_WAIT: Final = 30.0  # seconds, then doubling
LONGEST_WAIT: Final = 600.0  # seconds: a device waits ten minutes at most
MAX_FAILURES: Final = 20  # wrong codes of the run before the pairing closes for all
_MAX_ADDRESSES: Final = 64  # addresses remembered: the oldest is forgotten first


@dataclass(frozen=True, slots=True)
class Attempt:
    """The wrong codes of one address: how many, when the last, until when it waits."""

    address: str
    failures: int
    last: float  # wall clock (seconds since the epoch), for the PC's card
    until: float  # monotonic clock: no new code before


def wait_after(failures: int) -> float:
    """The wait after a given number of wrong codes from one address.

    Args:
        failures: Its wrong codes so far.

    Returns:
        0 up to `FREE_TRIES`, then `FIRST_WAIT` doubling, capped at `LONGEST_WAIT`.
    """
    if failures < FREE_TRIES:
        return 0.0
    doubled: float = FIRST_WAIT * 2.0 ** (failures - FREE_TRIES)
    return min(doubled, LONGEST_WAIT)


class Attempts:
    """The wrong codes of this server, per address, and their total."""

    __slots__ = ("by_address", "total")

    def __init__(self) -> None:
        """Start without any wrong code."""
        self.by_address: dict[str, Attempt] = {}
        self.total = 0

    @property
    def closed(self) -> bool:
        """Tell whether the run's ceiling is reached.

        Returns:
            True from `MAX_FAILURES` wrong codes on.
        """
        return self.total >= MAX_FAILURES

    def waiting(self, address: str) -> bool:
        """Tell whether an address must wait before typing again.

        Args:
            address: The device's address.

        Returns:
            True while its wait runs.
        """
        known = self.by_address.get(address)
        return known is not None and time.monotonic() < known.until

    def failed(self, address: str) -> None:
        """Count a wrong code of an address.

        Args:
            address: The device's address.
        """
        self.total += 1
        known = self.by_address.pop(address, None)
        failures = 1 if known is None else known.failures + 1
        until = time.monotonic() + wait_after(failures)
        self.by_address[address] = Attempt(address, failures, time.time(), until)
        while len(self.by_address) > _MAX_ADDRESSES:
            del self.by_address[next(iter(self.by_address))]

    def seen(self) -> None:
        """Forget the report (*It was me*): the waits and the run's total stay."""
        self.by_address = {
            address: replace(attempt, failures=0, last=0.0)
            for address, attempt in self.by_address.items()
            if time.monotonic() < attempt.until
        }

    def reopen(self) -> None:
        """Start again from nothing: the PC opened the pairing with a new code."""
        self.by_address.clear()
        self.total = 0

    def reported(self) -> list[dict[str, object]]:
        """The addresses that typed wrong codes, for the PC's card.

        Returns:
            Each with `address`, `failures` and `at` (milliseconds since the epoch).
        """
        return [
            {"address": a.address, "failures": a.failures, "at": int(a.last * 1000)}
            for a in self.by_address.values()
            if a.failures
        ]
