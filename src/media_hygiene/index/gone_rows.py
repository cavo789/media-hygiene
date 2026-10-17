"""Files an audit proved gone and did not follow: deleted, or on a disk unplugged.

Before `pruning` forgets a file the walk proves gone and `rematch` did not follow, what
the index knew of it is kept here: size, modification time, partial digest, the full
SHA-256 when known, its date and camera, the moment it was found gone. Only the user
can tell a deletion from a disk not plugged in: `review --gone` asks, `clean
--decisions` writes the answers to the journal and drops the rows. Not a row of
`PATH_TABLES`: a gone file has no path to follow. A row whose content is listed (same
size and partial digest, at any path) is dropped: moved back, or a copy still there.
Version 15.
"""

from __future__ import annotations

import sqlite3
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.hashing import partial_digest

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.scan.models import MediaFile

CREATE_GONE: Final = """
CREATE TABLE IF NOT EXISTS gone_files (
    path TEXT PRIMARY KEY,
    size INTEGER NOT NULL,
    mtime_ns INTEGER NOT NULL,
    partial_digest TEXT NOT NULL,
    full_digest TEXT,
    taken_at TEXT,
    camera TEXT,
    gone_at TEXT NOT NULL
)
"""
# The facts of a file about to be forgotten; one without its partial digest cannot be
# recognised if it comes back, so it is not kept.
_RECORD: Final = (
    "INSERT OR REPLACE INTO gone_files (path, size, mtime_ns, partial_digest,"
    " full_digest, taken_at, camera, gone_at)"
    " SELECT path, size, mtime_ns, partial_digest, full_digest, taken_at, camera, ?"
    " FROM files WHERE path = ? AND partial_digest IS NOT NULL"
)
_EVERY: Final = (
    "SELECT path, size, mtime_ns, partial_digest, full_digest, taken_at, camera,"
    " gone_at FROM gone_files ORDER BY gone_at, path"
)
_KEYS: Final = "SELECT size, mtime_ns, partial_digest, path FROM gone_files"
_COUNT: Final = "SELECT COUNT(*) FROM gone_files"
_DROP: Final = "DELETE FROM gone_files WHERE path = ?"

type _Key = tuple[int, str]


@dataclass(frozen=True, slots=True)
class GoneRecord:  # pylint: disable=too-many-instance-attributes
    """A file proven gone, as the index knew it (container path)."""

    path: str
    size: int
    mtime_ns: int
    partial_digest: str
    full_digest: str | None = None
    taken_at: str | None = None
    camera: str | None = None
    gone_at: str = ""  # ISO 8601, UTC


def record_gone(
    connection: sqlite3.Connection, paths: Iterable[str], when: datetime
) -> None:
    """Keep what the index knew of files proven gone, before they are forgotten.

    Args:
        connection: The index.
        paths: The files gone and not followed.
        when: The moment the walk proved it.
    """
    moment = when.isoformat(timespec="seconds")
    connection.executemany(_RECORD, [(moment, path) for path in paths])


def drop_reappeared(repository: FactsRepository, files: Sequence[MediaFile]) -> int:
    """Drop the rows whose content is listed: moved back, or still there as a copy.

    The same size at any path, then the same partial digest (from the index, else
    read: 128 KiB of the few files concerned). A copy still present keeps the content:
    remembering the deletion of its twin would set the copy aside, never "back".

    Args:
        repository: The index.
        files: Every file the walk listed.

    Returns:
        How many rows were dropped.
    """
    connection = repository.connection
    waiting: defaultdict[_Key, list[str]] = defaultdict(list)
    for size, _mtime, digest, path in connection.execute(_KEYS):
        waiting[size, digest].append(path)
    sizes = {size for size, _digest in waiting}
    dropped: list[str] = []
    for file in files:
        if file.size not in sizes:
            continue
        digest = repository.get(file).partial_digest or _partial(file)
        dropped += waiting.pop((file.size, digest or ""), [])
    drop_records(connection, dropped)
    return len(dropped)


def _partial(file: MediaFile) -> str | None:
    """Read a file's partial digest.

    Args:
        file: A file listed.

    Returns:
        The digest, or None when it cannot be read.
    """
    try:
        return partial_digest(file.path)
    except OSError:
        return None


def gone_records(connection: sqlite3.Connection) -> tuple[GoneRecord, ...]:
    """Every file gone waiting for an answer, the oldest found first.

    Args:
        connection: The index.

    Returns:
        The records.
    """
    return tuple(GoneRecord(*row) for row in connection.execute(_EVERY))


def gone_count(connection: sqlite3.Connection) -> int:
    """Count the files gone waiting for an answer.

    Args:
        connection: The index.

    Returns:
        The count.
    """
    (count,) = connection.execute(_COUNT).fetchone()
    return int(count)


def drop_records(connection: sqlite3.Connection, paths: Iterable[str]) -> None:
    """Drop the rows of files answered (or moved).

    Args:
        connection: The index.
        paths: Their container paths.
    """
    connection.executemany(_DROP, [(path,) for path in paths])


def forget_answered(index_file: Path | None, plan: CleanPlan) -> None:
    """Drop the records `review --gone` answered, once the clean journaled them.

    Args:
        index_file: The index, or None.
        plan: The plan executed, with its answers.
    """
    if index_file is None or not plan.gone:
        return
    with sqlite3.connect(index_file) as connection:
        drop_records(connection, (answer.record.path for answer in plan.gone))
    connection.close()
