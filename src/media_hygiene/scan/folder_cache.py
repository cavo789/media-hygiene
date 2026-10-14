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
    from collections.abc import Mapping
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
class KeptStats:
    """The stats a changed folder keeps, and the date its new listing takes."""

    stats: Mapping[str, CachedStat]
    listed_at: datetime


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

    def kept_stats(self, folder: Path, now: datetime) -> KeptStats:
        """The `stat` of the files of a changed folder that can still be trusted.

        A file rewritten in place does not change its folder's time: its `stat` is
        trusted until the listing is too old, whether or not other names came or went.
        The new listing keeps the date of the old one, so that a folder changing every
        day is still read in full once its last full reading is too old.

        Args:
            folder: A folder about to be listed again.
            now: The time of this walk.

        Returns:
            The `stat` of each file of its last listing, by name, and the date the new
            listing takes; none and `now` when that listing is too old or nothing is
            trusted.
        """
        known = self.known.get(folder)
        if known is None or self.trusted_since is None:
            return KeptStats({}, now)
        if known.listed_at < self.trusted_since:
            return KeptStats({}, now)
        stats = {
            entry.name: entry.facts
            for entry in known.entries
            if entry.kind is EntryKind.FILE and entry.facts is not None
        }
        return KeptStats(stats, known.listed_at if stats else now)


def cached_entry(
    entry: os.DirEntry[str], kept: Mapping[str, CachedStat]
) -> CachedEntry:
    """Record one entry of a folder just listed.

    Args:
        entry: The entry.
        kept: The `stat` of the files the last listing saw, by name, still trusted.

    Returns:
        It, with the `stat` of a regular file: the kept one while the name still
        holds the same inode (`readdir` gives it for free; an editor saving through a
        new file and a rename gives a new one), else read now (None when that fails).
    """
    if entry.is_dir(follow_symlinks=False):
        return CachedEntry(entry.path, entry.name, EntryKind.DIR)
    if not entry.is_file(follow_symlinks=False):
        return CachedEntry(entry.path, entry.name, EntryKind.OTHER)
    known = kept.get(entry.name)
    if known is not None and known.st_ino == entry.inode():  # not saved as a new file
        return CachedEntry(entry.path, entry.name, EntryKind.FILE, known)
    try:
        stat = entry.stat(follow_symlinks=False)
    except OSError:
        return CachedEntry(entry.path, entry.name, EntryKind.FILE)
    facts = CachedStat(stat.st_size, stat.st_mtime_ns, stat.st_dev, stat.st_ino)
    return CachedEntry(entry.path, entry.name, EntryKind.FILE, facts)
