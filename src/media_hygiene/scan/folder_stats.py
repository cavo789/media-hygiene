"""Record a folder just listed: its files `stat`ed in parallel, known ones kept.

Through a Windows drive seen by Docker, one `stat` waits ≈ 1 ms; sixteen at once cost
≈ 0.1 ms per file (measured, TODO 0153). A folder of 100,000 photos read in one thread
took ≈ 107 s: its files are now `stat`ed in batches, within the walk's I/O limit. A
folder that changed keeps the `stat` of the files its last listing saw, while that
listing is recent enough (`WalkSetup.kept_stats`): only its new names are `stat`ed.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.folder_cache import FolderListing, cached_entry

if TYPE_CHECKING:
    import os
    from collections.abc import Mapping, Sequence
    from datetime import datetime

    from media_hygiene.scan.folder_cache import CachedEntry, CachedStat

# Entries `stat`ed by one thread in a row: enough to amortise the hand-over.
_BATCH: Final = 256


@dataclass(frozen=True, slots=True)
class StatPlan:
    """How to record one folder: its time, when, the stats kept, the I/O limit."""

    mtime_ns: int
    listed_at: datetime
    kept: Mapping[str, CachedStat]
    slots: asyncio.Semaphore


async def fresh_listing(
    items: Sequence[os.DirEntry[str]], plan: StatPlan
) -> FolderListing:
    """Record the entries of a folder, `stat`ing its files in parallel batches.

    Args:
        items: Its entries, as `os.scandir` gave them.
        plan: Its time, when it was listed, the stats kept, the I/O limit.

    Returns:
        The listing, its entries in the order of `items`.
    """

    async def batch(part: Sequence[os.DirEntry[str]]) -> list[CachedEntry]:
        """Record a batch of entries in a worker thread.

        Args:
            part: The entries.

        Returns:
            Their records.
        """
        async with plan.slots:
            return await asyncio.to_thread(_recorded, part, plan.kept)

    parts = [items[start : start + _BATCH] for start in range(0, len(items), _BATCH)]
    async with asyncio.TaskGroup() as group:
        tasks = [group.create_task(batch(part)) for part in parts]
    entries = tuple(entry for task in tasks for entry in task.result())
    return FolderListing(plan.mtime_ns, plan.listed_at, entries)


def _recorded(
    part: Sequence[os.DirEntry[str]], kept: Mapping[str, CachedStat]
) -> list[CachedEntry]:
    """Record entries one after the other (runs in a worker thread).

    Args:
        part: The entries.
        kept: The stats still trusted, by name.

    Returns:
        Their records.
    """
    return [cached_entry(entry, kept) for entry in part]
