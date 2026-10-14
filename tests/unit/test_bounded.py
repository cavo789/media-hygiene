"""A fixed number of workers over many files: order kept, concurrency bounded (0151)."""

from __future__ import annotations

import asyncio

import pytest

from media_hygiene.scan.bounded import bounded_map, pool_in_flight

_LIMIT = 3


def test_results_keep_the_order_and_the_limit() -> None:
    """Every item gets its result, in order, never more than `limit` at once."""
    running = 0
    peak = 0

    async def work(item: int) -> int:
        nonlocal running, peak
        running += 1
        peak = max(peak, running)
        await asyncio.sleep(0.001 * (item % 4))
        running -= 1
        return item * 2

    items = list(range(50))
    assert asyncio.run(bounded_map(items, work, _LIMIT)) == [i * 2 for i in items]
    assert peak == _LIMIT


def test_nothing_to_do() -> None:
    """No item, no worker."""

    async def work(item: int) -> int:
        return item

    assert asyncio.run(bounded_map([], work, _LIMIT)) == []


def test_a_failure_ends_the_pass() -> None:
    """As with one task per file: the error comes back in an `ExceptionGroup`."""

    async def work(item: int) -> int:
        if item == 5:
            raise ValueError(item)
        await asyncio.sleep(0)
        return item

    with pytest.raises(ExceptionGroup):
        asyncio.run(bounded_map(list(range(20)), work, _LIMIT))


def test_the_pool_always_has_work_at_hand() -> None:
    """At least two files per process, never fewer than the I/O limit."""
    assert pool_in_flight() >= 2
