"""Run an asynchronous step over many files with a fixed number of workers.

One task per file, all created at once, costs about 4.4 KB per file at the peak once
they are handed to a pool (measured: 1.3 GB for 300,000 files, TODO 0151). A few
workers pulling from one shared iterator keep the same concurrency for a bounded cost.
A failure of one file ends the pass as a `TaskGroup` does: the others are cancelled,
an `ExceptionGroup` is raised.
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable, Sequence

# Files kept in flight per process of the pool: it always has the next one at hand.
_PER_PROCESS = 2


def pool_in_flight() -> int:
    """How many files a pass hands out at once when it uses the process pool.

    Returns:
        Twice the CPUs (the pool has one process per CPU), at least the I/O limit:
        videos of the same pass wait on `ffprobe`, not on the pool.
    """
    return max(_PER_PROCESS * (os.process_cpu_count() or 1), Sizes.IO_CONCURRENCY)


async def bounded_map[T, R](
    items: Sequence[T], work: Callable[[T], Awaitable[R]], limit: int
) -> list[R]:
    """Await `work` on every item, at most `limit` at a time.

    Args:
        items: The items, in order.
        work: The step for one item.
        limit: How many items are in flight at most.

    Returns:
        The results, in the order of `items`.
    """
    results: dict[int, R] = {}
    pending = iter(enumerate(items))

    async def worker() -> None:
        """Take the next item until none is left (one event loop: no race)."""
        for index, item in pending:
            results[index] = await work(item)

    async with asyncio.TaskGroup() as group:
        workers = [group.create_task(worker()) for _ in range(min(limit, len(items)))]
    del workers  # all awaited by the group
    return [results[index] for index in range(len(items))]
