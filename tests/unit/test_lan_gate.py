"""The home network's doors: caps, a short head time, the PC unchanged (0682)."""

from __future__ import annotations

import asyncio
import contextlib
import time
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response
from media_hygiene.review.lan_gate import (
    HEAD_SECONDS,
    PER_ADDRESS,
    PER_DOOR,
    DoorGate,
    gated,
)
from media_hygiene.review.serving import Served, serve_connection, serve_within

if TYPE_CHECKING:
    from collections.abc import AsyncIterator, Awaitable, Callable

    from media_hygiene.review.http import Request

_LOOPBACK: Final = "127.0.0.1"
_IDLE: Final = 500  # idle connections a misbehaving device opens
_BROWSER: Final = 6  # parallel connections of a browser to one host
_TILES: Final = 200  # a page of tiles: one request each
_PC_ANSWERS_WITHIN: Final = 1.0  # seconds: the PC's page as usual
_REQUEST: Final = b"GET / HTTP/1.1\r\nHost: x\r\n\r\n"


async def _ok(_request: Request) -> Response:
    return Response(HTTPStatus.OK, b"ok")


@contextlib.asynccontextmanager
async def _server(
    handler: Callable[[asyncio.StreamReader, asyncio.StreamWriter], Awaitable[None]],
) -> AsyncIterator[int]:
    server = await asyncio.start_server(handler, _LOOPBACK, 0, backlog=1024)
    async with server:
        yield server.sockets[0].getsockname()[1]


def _lan(gate: DoorGate) -> Callable[..., Awaitable[None]]:
    served = Served(_ok, HEAD_SECONDS)
    return gated(gate, lambda reader, writer: serve_within(reader, writer, served))


async def _get(port: int) -> bytes:
    reader, writer = await asyncio.open_connection(_LOOPBACK, port)
    writer.write(_REQUEST)
    await writer.drain()
    answer = await reader.read()
    writer.close()
    await writer.wait_closed()
    return answer


async def _all_decided(gate: DoorGate) -> None:
    """Wait until the gate has admitted or refused every idle connection."""
    for _round in range(1000):
        refused = sum(int(str(r["count"])) for r in gate.reported())
        if gate.open + refused >= _IDLE:
            return
        await asyncio.sleep(0.01)


def test_the_caps_per_address_and_per_door() -> None:
    """Beyond either cap a connection is refused and counted; a leave frees a seat."""
    gate = DoorGate()
    assert all(gate.enter("a") for _n in range(PER_ADDRESS))
    assert not gate.enter("a")
    for index in range(PER_DOOR - PER_ADDRESS):
        assert gate.enter(f"b{index}")
    assert not gate.enter("c")  # the door is full: another device waits too
    gate.leave("a")
    assert gate.enter("c")
    assert {r["address"]: r["count"] for r in gate.reported()} == {"a": 1, "c": 1}
    gate.seen()
    assert gate.reported() == []


def test_the_caps_leave_room_for_phones_and_a_tv_behind_one_gateway() -> None:
    """Docker Desktop may show every device with one address: 6 phones and a TV."""
    assert PER_ADDRESS >= 7 * _BROWSER
    assert PER_DOOR >= 2 * PER_ADDRESS


def test_500_idle_connections_never_stop_the_pc() -> None:
    """The surplus is refused at once; the PC's door answers within its usual time."""
    gate = DoorGate()

    async def scenario() -> tuple[float, bytes]:
        async with (
            _server(_lan(gate)) as lan,
            _server(lambda r, w: serve_connection(r, w, _ok)) as pc,
        ):
            idle = await asyncio.gather(
                *(asyncio.open_connection(_LOOPBACK, lan) for _n in range(_IDLE))
            )
            try:
                await _all_decided(gate)
                started = time.monotonic()
                answer = await _get(pc)
                return time.monotonic() - started, answer
            finally:
                for _reader, writer in idle:
                    writer.close()
                await asyncio.gather(
                    *(w.wait_closed() for _r, w in idle), return_exceptions=True
                )

    took, answer = asyncio.run(asyncio.wait_for(scenario(), 10))
    assert answer.startswith(b"HTTP/1.1 200")
    assert took < _PC_ANSWERS_WITHIN
    assert gate.open == 0
    refused = gate.reported()
    assert [r["count"] for r in refused] == [_IDLE - PER_ADDRESS]


def test_a_page_of_tiles_over_six_connections_is_never_refused() -> None:
    """200 tiles over a browser's 6 connections from one address: all served."""
    gate = DoorGate()

    async def scenario() -> list[bytes]:
        async with _server(_lan(gate)) as lan:
            queue = list(range(_TILES))
            answers: list[bytes] = []

            async def browser_connection() -> None:
                while queue:
                    queue.pop()
                    answers.append(await _get(lan))

            async with asyncio.TaskGroup() as group:
                for _n in range(_BROWSER):
                    group.create_task(browser_connection())
            return answers

    answers = asyncio.run(asyncio.wait_for(scenario(), 20))
    assert len(answers) == _TILES
    assert all(a.startswith(b"HTTP/1.1 200") for a in answers)
    assert gate.reported() == []
    assert gate.open == 0


def test_a_silent_head_is_dropped_sooner_on_the_lan() -> None:
    """A connection that sends nothing is closed after the door's head time."""
    head: Final = 0.1
    gate = DoorGate()

    async def scenario() -> tuple[float, bytes]:
        served = Served(_ok, head)
        handler = gated(gate, lambda r, w: serve_within(r, w, served))
        async with _server(handler) as lan:
            reader, writer = await asyncio.open_connection(_LOOPBACK, lan)
            started = time.monotonic()
            closed = await reader.read()  # the server closes: nothing was asked
            writer.close()
            return time.monotonic() - started, closed

    took, closed = asyncio.run(asyncio.wait_for(scenario(), 5))
    assert closed == b""
    assert took < 2
