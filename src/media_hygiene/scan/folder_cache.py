"""What a folder held when last listed: reused while the folder did not change.

A folder's modification time changes when an entry is added, removed or renamed in
it. While it stays the same, the walk takes the folder's entries from the index
instead of listing it and `stat`ing every file again: on a Windows drive seen through
Docker, that `stat` is most of the walk. A file rewritten in place (same name) does not
change its folder's time: a listing older than `[scan] full_check_days` is read again
whatever its time, and `audit --full` reads everything.
"""

from __future__ import annotations

import errno
import os
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.scan.filters import ScanFilters


class EntryKind(StrEnum):
    """What a folder entry is, links not followed."""

    DIR = "dir"
    FILE = "file"
    OTHER = "other"  # a link, a device: never walked


@dataclass(frozen=True, slots=True)
class CachedStat:
    """The few `stat` fields the walk reads."""

    st_size: int
    st_mtime_ns: int
    st_dev: int
    st_ino: int


@dataclass(frozen=True, slots=True)
class CachedEntry:
    """A folder entry as last listed; reads like an `os.DirEntry` for the walk."""

    path: str
    name: str
    kind: EntryKind
    facts: CachedStat | None = None  # files only; None: it could not be `stat`ed

    def is_dir(self, *, follow_symlinks: bool = True) -> bool:
        """Tell whether the entry is a folder (links were never followed).

        Args:
            follow_symlinks: Ignored, as for the listing.

        Returns:
            True for a folder.
        """
        del follow_symlinks  # links were never followed
        return self.kind is EntryKind.DIR

    def is_file(self, *, follow_symlinks: bool = True) -> bool:
        """Tell whether the entry is a regular file.

        Args:
            follow_symlinks: Ignored, as for the listing.

        Returns:
            True for a regular file.
        """
        del follow_symlinks  # links were never followed
        return self.kind is EntryKind.FILE

    def stat(self, *, follow_symlinks: bool = True) -> CachedStat:
        """The size, time and identity the listing saw.

        Args:
            follow_symlinks: Ignored, as for the listing.

        Returns:
            Them.

        Raises:
            OSError: The listing could not `stat` the file either.
        """
        del follow_symlinks  # links were never followed
        if self.facts is None:
            raise OSError(errno.EIO, os.strerror(errno.EIO), self.path)
        return self.facts


@dataclass(frozen=True, slots=True)
class FolderListing:
    """A folder's entries, its modification time then, and when it was listed."""

    mtime_ns: int
    listed_at: datetime
    entries: tuple[CachedEntry, ...]


@dataclass(frozen=True, slots=True)
class WalkSetup:
    """What a walk keeps, and the listings it may trust instead of reading a folder.

    `trusted_since`: a listing older than this is read again; None trusts nothing.
    """

    filters: ScanFilters
    known: Mapping[Path, FolderListing] = field(default_factory=dict)
    trusted_since: datetime | None = None

    def reusable(self, folder: Path, mtime_ns: int) -> FolderListing | None:
        """The listing of a folder that did not change since, and is recent enough.

        Args:
            folder: The folder.
            mtime_ns: Its modification time now.

        Returns:
            The listing, or None: the folder is to be read.
        """
        known = self.known.get(folder)
        if known is None or self.trusted_since is None:
            return None
        if known.mtime_ns != mtime_ns or known.listed_at < self.trusted_since:
            return None
        return known


def snapshot(
    entries: Sequence[os.DirEntry[str]], mtime_ns: int, now: datetime
) -> FolderListing:
    """Record a folder just listed, every regular file `stat`ed.

    Args:
        entries: Its entries.
        mtime_ns: Its modification time, read before listing it.
        now: When it was listed.

    Returns:
        The listing.
    """
    return FolderListing(mtime_ns, now, tuple(_cached(entry) for entry in entries))


def _cached(entry: os.DirEntry[str]) -> CachedEntry:
    """Record one entry.

    Args:
        entry: The entry.

    Returns:
        It, with the `stat` of a regular file (None when it fails).
    """
    if entry.is_dir(follow_symlinks=False):
        return CachedEntry(entry.path, entry.name, EntryKind.DIR)
    if not entry.is_file(follow_symlinks=False):
        return CachedEntry(entry.path, entry.name, EntryKind.OTHER)
    try:
        stat = entry.stat(follow_symlinks=False)
    except OSError:
        return CachedEntry(entry.path, entry.name, EntryKind.FILE)
    facts = CachedStat(stat.st_size, stat.st_mtime_ns, stat.st_dev, stat.st_ino)
    return CachedEntry(entry.path, entry.name, EntryKind.FILE, facts)
