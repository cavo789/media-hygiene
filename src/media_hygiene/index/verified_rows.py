"""When each file was last read in full, and the files found damaged (0690, version 20).

The audit trusts a file whose size and modification time did not change: a disk that
silently damages a file changes neither. The slow re-read (`services.reread`) reads
the files whose last full read is oldest, and keeps here, per path, the version read
(size, mtime), its SHA-256 (`digest`, the content known good) and when (`verified_at`).
A later read of the same version with another SHA-256 is never an edit: the row keeps
the good digest, `found` the one read, `damaged_since` the day it was found. A row of
another version (an edit, `touch`) is a new start. Keyed by path, a table of
`PATH_TABLES`: it follows a file `sort` or `undo` moves, leaves with a file the audit
or `clean` forgets, and is parked with a file set aside.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

CREATE_VERIFIED: Final = """
CREATE TABLE IF NOT EXISTS verified (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    digest TEXT NOT NULL,
    verified_at TEXT NOT NULL,
    damaged_since TEXT,
    found TEXT
)
"""
# Every file of the index, the never read first, then the oldest read.
_OLDEST: Final = """
SELECT f.path, f.size, f.mtime_ns, f.partial_digest, f.full_digest,
       v.size, v.mtime_ns, v.digest, v.damaged_since
FROM files f LEFT JOIN verified v ON v.path = f.path
ORDER BY v.verified_at IS NOT NULL, v.verified_at, f.path
"""
_GOOD: Final = (
    "INSERT OR REPLACE INTO verified (path, size, mtime_ns, digest, verified_at,"
    " damaged_since, found) VALUES (?, ?, ?, ?, ?, NULL, NULL)"
)
_DAMAGED: Final = (
    "INSERT INTO verified (path, size, mtime_ns, digest, verified_at, damaged_since,"
    " found) VALUES (?, ?, ?, ?, ?, ?, ?) ON CONFLICT (path) DO UPDATE SET"
    " size = excluded.size, mtime_ns = excluded.mtime_ns, digest = excluded.digest,"
    " damaged_since = COALESCE(verified.damaged_since, excluded.damaged_since),"
    " found = excluded.found"
)
_EVERY_DAMAGED: Final = (
    "SELECT path, size, mtime_ns, digest, verified_at, damaged_since, found"
    " FROM verified WHERE damaged_since IS NOT NULL ORDER BY path"
)


@dataclass(frozen=True, slots=True)
class Known:
    """What the index knows of one file before it is read again."""

    path: str
    size: int
    mtime_ns: int
    partial: str | None  # the audit's digests of this version
    full: str | None
    read: tuple[int, int, str] | None  # the version last read in full, its digest
    damaged_since: str | None


@dataclass(frozen=True, slots=True)
class Reading:
    """One full read of a file: the version read, its SHA-256 and the good one."""

    path: str
    stat: tuple[int, int]
    digest: str  # the content known good
    at: str


@dataclass(frozen=True, slots=True)
class Damaged:
    """A file whose content changed while its size and time did not."""

    path: str
    size: int
    mtime_ns: int
    digest: str  # the content known good
    verified_at: str  # the last day it was read fine (or its first reading)
    damaged_since: str
    found: str


def oldest_first(connection: sqlite3.Connection) -> list[Known]:
    """Every file of the index, the one read in full longest ago first.

    Args:
        connection: The index.

    Returns:
        What is known of each.
    """
    return [
        Known(
            path,
            size,
            mtime,
            partial,
            full,
            None if digest is None else (read_size, read_mtime, digest),
            since,
        )
        for (
            path,
            size,
            mtime,
            partial,
            full,
            read_size,
            read_mtime,
            digest,
            since,
        ) in connection.execute(_OLDEST)
    ]


def note_good(connection: sqlite3.Connection, reading: Reading) -> None:
    """Remember a file read fine (or read for the first time): no damage.

    Args:
        connection: The index.
        reading: The read.
    """
    size, mtime = reading.stat
    connection.execute(_GOOD, (reading.path, size, mtime, reading.digest, reading.at))


def note_damaged(connection: sqlite3.Connection, reading: Reading, found: str) -> None:
    """Remember a file found damaged; the day first found and the good digest stay.

    Args:
        connection: The index.
        reading: The read, `digest` the content known good, `at` today.
        found: The SHA-256 read now.
    """
    size, mtime = reading.stat
    connection.execute(
        _DAMAGED,
        (reading.path, size, mtime, reading.digest, reading.at, reading.at, found),
    )


def damaged_files(connection: sqlite3.Connection) -> list[Damaged]:
    """Every file found damaged and not repaired since.

    Args:
        connection: The index.

    Returns:
        Them, by path.
    """
    return [Damaged(*row) for row in connection.execute(_EVERY_DAMAGED)]
