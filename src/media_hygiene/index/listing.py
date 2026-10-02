"""Read the whole index back: every file it describes, its roots, its duplicate digests.

Used by `inventory`, which exports what the audits learnt without reading any file
again. Rows are streamed in path order: 70,000 files never sit in memory at once.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.rows import facts_of
from media_hygiene.index.schema import EVERY_FILE

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterator

    from media_hygiene.index.facts import FileFacts

_COUNT: Final = "SELECT COUNT(*) FROM files"
_ROOTS: Final = "SELECT path, walked_at FROM roots ORDER BY path"
# Digests shared by several files: the duplicate groups, numbered by their first path.
_SHARED: Final = (
    "SELECT full_digest, COUNT(*), MIN(path) FROM files"
    " WHERE full_digest IS NOT NULL GROUP BY full_digest HAVING COUNT(*) > 1"
    " ORDER BY MIN(path)"
)


@dataclass(frozen=True, slots=True)
class IndexedFile:
    """One file of the index: where it is, its size and mtime, and its facts."""

    path: Path
    size: int
    mtime_ns: int
    facts: FileFacts


@dataclass(frozen=True, slots=True)
class WalkedRoot:
    """A mounted folder, and when an audit last walked it without a read error."""

    path: Path
    walked_at: datetime


@dataclass(frozen=True, slots=True)
class SharedDigest:
    """A SHA-256 shared by several files: its group number and its number of copies."""

    group: int
    copies: int


def count_files(connection: sqlite3.Connection) -> int:
    """Count the files of the index.

    Args:
        connection: An open index.

    Returns:
        The number of rows.
    """
    row = connection.execute(_COUNT).fetchone()
    return int(row[0]) if row else 0


def indexed_files(connection: sqlite3.Connection) -> Iterator[IndexedFile]:
    """Stream every file of the index, in path order.

    Args:
        connection: An open index.

    Yields:
        The files and their facts.
    """
    for row in connection.execute(EVERY_FILE):
        path, size, mtime_ns = row[0], row[1], row[2]
        yield IndexedFile(Path(path), int(size), int(mtime_ns), facts_of(row[1:]))


def walked_roots(connection: sqlite3.Connection) -> tuple[WalkedRoot, ...]:
    """List the folders an audit walked completely, and when.

    Args:
        connection: An open index.

    Returns:
        The roots, in path order.
    """
    return tuple(
        WalkedRoot(Path(path), datetime.fromisoformat(walked_at))
        for path, walked_at in connection.execute(_ROOTS)
    )


def shared_digests(connection: sqlite3.Connection) -> dict[str, SharedDigest]:
    """Number the SHA-256 digests shared by several files.

    Args:
        connection: An open index.

    Returns:
        Digest → its group (from 1, in the order of its first path) and copies.
    """
    return {
        digest: SharedDigest(number, int(copies))
        for number, (digest, copies, _first) in enumerate(
            connection.execute(_SHARED), start=1
        )
    }
