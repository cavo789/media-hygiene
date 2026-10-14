"""List every media file and sidecar below the data roots, without following links.

Folders are read concurrently: on a Windows drive seen through Docker, each directory
listing waits for a slow round trip, so several are kept in flight at once. A folder
that did not change since the index last listed it is taken from the index instead
(`scan.folder_cache`): one `stat` of the folder instead of one per file. A folder read
again has its files `stat`ed in parallel, and only its new names when the last listing
is recent enough (`scan.folder_stats`).
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass, field
from datetime import UTC, datetime
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.constants import ALBUM_MARKER, Sizes
from media_hygiene.scan.folder_cache import EntryKind
from media_hygiene.scan.folder_entries import Listing, sort_entries
from media_hygiene.scan.folder_stats import StatPlan, fresh_listing

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.scan.filters import ScanFilters
    from media_hygiene.scan.folder_cache import CachedEntry, FolderListing, WalkSetup
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.scan.sidecars import Sidecar

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class Walk:
    """What the walk found below the roots, in no fixed order.

    `unreadable` lists the folders it could not read and the files it could not
    `stat`: whatever lies there may exist, the walk just could not see it.
    `listings`: the folders read this time, to keep in the index; `visited`: every
    folder walked; `reused`: how many of them came from the index.
    """

    files: tuple[MediaFile, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    unreadable: tuple[Path, ...] = ()
    listings: Mapping[Path, FolderListing] = field(
        default_factory=lambda: MappingProxyType({})
    )
    visited: frozenset[Path] = frozenset()
    reused: int = 0


@dataclass(frozen=True, slots=True)
class _Visit:
    """One folder walked: what it holds, its new listing, whether it was reused."""

    listing: Listing
    fresh: FolderListing | None = None
    reused: bool = False


@dataclass(frozen=True, slots=True)
class _Read:
    """A folder read in a worker thread: done, or its entries still to record."""

    done: _Visit | None = None
    mtime_ns: int = 0
    items: tuple[os.DirEntry[str], ...] = ()


async def walk(
    roots: Iterable[Path],
    setup: WalkSetup,
    progress: ProgressSink,
) -> Walk:
    """Return the media files and sidecars below `roots`, as `setup` allows.

    Unreadable folders and files are logged, skipped and listed: one bad folder
    never stops the scan.
    Nested or overlapping roots list their files twice: see `unique_files`.
    Sidecars are listed whatever the extension filter: they follow their photo.

    Args:
        roots: Folders to walk.
        setup: Folders to skip, extensions to keep, the listings to trust.
        progress: Advanced once per media file found.

    Returns:
        Every media file and sidecar found, what could not be read, the new listings.
    """
    files: list[MediaFile] = []
    sidecars: list[Sidecar] = []
    unreadable: list[Path] = []
    listings: dict[Path, FolderListing] = {}
    visited: list[Path] = []
    reused = 0
    now = datetime.now(UTC)
    visits: list[asyncio.Task[None]] = []
    slots = asyncio.Semaphore(Sizes.IO_CONCURRENCY)
    async with asyncio.TaskGroup() as group:

        async def visit(folder: Path) -> None:
            nonlocal reused
            async with slots:
                read = await asyncio.to_thread(_read, folder, setup)
            seen = read.done or await _fresh(folder, read, (setup, now, slots))
            listing = seen.listing
            files.extend(listing.files)
            sidecars.extend(listing.sidecars)
            unreadable.extend(listing.unreadable)
            visited.append(folder)
            reused += seen.reused
            if seen.fresh is not None:
                listings[folder] = seen.fresh
            for _file in listing.files:
                progress.advance()
            visits.extend(group.create_task(visit(sub)) for sub in listing.folders)

        visits.extend(group.create_task(visit(root)) for root in roots)
    found = (tuple(files), tuple(sidecars), tuple(unreadable))
    return Walk(*found, MappingProxyType(listings), frozenset(visited), reused)


def _read(folder: Path, setup: WalkSetup) -> _Read:
    """Read one folder, or take it from the index (runs in a worker thread).

    Args:
        folder: Folder to read.
        setup: What to keep and trust.

    Returns:
        What it holds when taken from the index or unreadable; else its entries,
        still to record.
    """
    try:
        mtime_ns = folder.stat().st_mtime_ns  # before listing: a later change shows
        known = setup.reusable(folder, mtime_ns)
        if known is not None:
            return _Read(_Visit(_sorted(known.entries, setup.filters), reused=True))
        with os.scandir(folder) as entries:
            items = tuple(entries)
    except OSError as exc:
        _LOGGER.warning("Cannot read folder %s: %s", folder, exc.strerror)
        return _Read(_Visit(Listing(unreadable=(folder,))))
    return _Read(mtime_ns=mtime_ns, items=items)


async def _fresh(
    folder: Path, read: _Read, context: tuple[WalkSetup, datetime, asyncio.Semaphore]
) -> _Visit:
    """Record a folder just listed: its files `stat`ed in parallel, known ones kept.

    Args:
        folder: The folder.
        read: Its time and entries.
        context: What to keep and trust, the time of this walk, the I/O limit.

    Returns:
        What it holds, and its listing to keep when every file could be `stat`ed.
    """
    setup, now, slots = context
    kept = setup.kept_stats(folder, now)
    plan = StatPlan(read.mtime_ns, kept.listed_at, kept.stats, slots)
    fresh = await fresh_listing(read.items, plan)
    complete = all(
        entry.facts is not None
        for entry in fresh.entries
        if entry.kind is EntryKind.FILE
    )
    return _Visit(_sorted(fresh.entries, setup.filters), fresh if complete else None)


def _sorted(entries: Sequence[CachedEntry], filters: ScanFilters) -> Listing:
    """Sort the entries of a folder, unless it is an album.

    Args:
        entries: Its entries.
        filters: Folders to skip and extensions to keep.

    Returns:
        Its media files, sidecars and subfolders; nothing for an album, whose files
        are second names of files listed where they are.
    """
    if any(entry.name == ALBUM_MARKER for entry in entries):
        return Listing()
    return sort_entries(entries, filters)
