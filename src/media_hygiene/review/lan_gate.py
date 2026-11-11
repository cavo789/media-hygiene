"""The home network's doors: how many connections at once, refused ones reported (0682).

One device on the Wi-Fi opening thousands of idle connections held as many tasks and
file descriptors, and the PC's own page (same process) stopped answering. On the doors
of the home network only (the PC's loopback is unchanged), a connection beyond
`PER_ADDRESS` open from one address, or `PER_DOOR` open in all, is closed at once,
counted per address, and said on the PC's card. Such a door also gives `HEAD_SECONDS`
to send the request line and headers (the body keeps its 30 s) and `HANDSHAKE_SECONDS`
to the TLS handshake. Constants, not settings: no collection changes them.

Sizing: a browser opens at most 6 connections to one host, and each answer closes its
connection, so a phone loading a 200-tile page holds 6 at most. Docker Desktop may show
every device with one gateway address: `PER_ADDRESS` then covers all of them together,
several phones and a TV (about 6 each) under it.
"""

from __future__ import annotations

import contextlib
import time
from dataclasses import dataclass
from functools import cache
from typing import TYPE_CHECKING, Final

from media_hygiene.review.serving import peer_of

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Awaitable, Callable

    type Serve = Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]]

PER_ADDRESS: Final = 48  # open connections of one address: 8 devices of 6 behind one
PER_DOOR: Final = 128  # open connections of the home network's doors together
HEAD_SECONDS: Final = 5.0  # to send the request line and the headers
HANDSHAKE_SECONDS: Final = 10.0  # TLS handshake (asyncio's default: 60 s)
_MAX_ADDRESSES: Final = 64  # refused addresses remembered: the oldest forgotten first


@dataclass(slots=True)
class Refusals:
    """The connections refused to one address: how many, when the last."""

    address: str
    count: int
    last: float  # wall clock, for the PC's card


class DoorGate:
    """The open connections of the home network's doors, and the refused ones."""

    __slots__ = ("by_address", "open", "refused")

    def __init__(self) -> None:
        """Start without any connection."""
        self.by_address: dict[str, int] = {}
        self.open = 0
        self.refused: dict[str, Refusals] = {}

    def enter(self, address: str) -> bool:
        """Let a connection in, or count it refused.

        Args:
            address: The device's address, from the socket.

        Returns:
            True when it may be served; False beyond a cap (counted).
        """
        held = self.by_address.get(address, 0)
        if held >= PER_ADDRESS or self.open >= PER_DOOR:
            self._refuse(address)
            return False
        self.by_address[address] = held + 1
        self.open += 1
        return True

    def leave(self, address: str) -> None:
        """Forget a connection served.

        Args:
            address: The device's address.
        """
        held = self.by_address.pop(address, 1) - 1
        if held > 0:
            self.by_address[address] = held
        self.open -= 1

    def _refuse(self, address: str) -> None:
        """Count a refused connection.

        Args:
            address: The device's address.
        """
        known = self.refused.pop(address, None) or Refusals(address, 0, 0.0)
        known.count += 1
        known.last = time.time()
        self.refused[address] = known  # last refused, last in the order
        while len(self.refused) > _MAX_ADDRESSES:
            del self.refused[next(iter(self.refused))]

    def seen(self) -> None:
        """Put the report away: the PC's *It was me*."""
        self.refused.clear()

    def reported(self) -> list[dict[str, object]]:
        """The addresses refused, for the PC's card.

        Returns:
            Each with `address`, `count` and `at` (milliseconds since the epoch).
        """
        return [
            {"address": r.address, "count": r.count, "at": int(r.last * 1000)}
            for r in self.refused.values()
        ]


@cache
def lan_gate() -> DoorGate:
    """The process's gate: one home network door per process, read by the PC's card.

    Returns:
        The same gate on every call.
    """
    return DoorGate()


def gated(gate: DoorGate, serve: Serve) -> Serve:
    """Serve a connection through the gate: closed at once beyond a cap.

    Args:
        gate: The doors' counts.
        serve: Serves an admitted connection.

    Returns:
        The connection's handler for `asyncio.start_server`.
    """

    async def connection(
        reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Admit or refuse one connection.

        Args:
            reader: What the device sends.
            writer: Where to answer.
        """
        address = peer_of(writer)
        if not gate.enter(address):
            writer.close()
            with contextlib.suppress(ConnectionError):
                await writer.wait_closed()
            return
        try:
            await serve(reader, writer)
        finally:
            gate.leave(address)

    return connection
