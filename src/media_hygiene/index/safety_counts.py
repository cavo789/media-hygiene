"""Count what the *Are my photos safe?* card reads from the index, read-only (0689)."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from pathlib import Path

_FILES: Final = "SELECT COUNT(*) FROM files"
_READ: Final = (
    "SELECT COUNT(*), MIN(verified_at),"
    " COALESCE(SUM(damaged_since IS NOT NULL), 0) FROM verified"
)
_NEWER: Final = "SELECT COUNT(*) FROM files WHERE mtime_ns > ?"


@dataclass(frozen=True, slots=True)
class RereadCounts:
    """How far `audit --reread` went (0690)."""

    files: int  # in the index
    read: int  # read again at least once
    damaged: int  # found damaged, not repaired since
    oldest: str | None  # the oldest reading kept, ISO 8601


def reread_counts(index_file: Path | None) -> RereadCounts | None:
    """Count the files of the index, those read again, those found damaged.

    Args:
        index_file: The index, None when the cache is not mounted.

    Returns:
        The counts; None without an index. An index older than the re-read
        counts no file read.
    """
    if index_file is None or not index_file.is_file():
        return None
    try:
        with closing(connect_read_only(index_file)) as connection:
            files = int(connection.execute(_FILES).fetchone()[0])
            try:
                read, oldest, damaged = connection.execute(_READ).fetchone()
            except sqlite3.OperationalError:  # no `verified` table yet
                read, oldest, damaged = 0, None, 0
    except sqlite3.Error:
        return None
    return RereadCounts(files, int(read), int(damaged), oldest)


def newer_than(index_file: Path | None, mtime_ns: int) -> int | None:
    """Count the files of the index changed after a moment.

    Args:
        index_file: The index, None when the cache is not mounted.
        mtime_ns: The moment, in nanoseconds since the epoch.

    Returns:
        Them; None without an index.
    """
    if index_file is None or not index_file.is_file():
        return None
    try:
        with closing(connect_read_only(index_file)) as connection:
            return int(connection.execute(_NEWER, (mtime_ns,)).fetchone()[0])
    except sqlite3.Error:
        return None
