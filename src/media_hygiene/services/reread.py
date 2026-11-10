"""`audit --reread`: read again in full the files read longest ago (0690).

Within `[routine] reread_gb` per run, the never-read files first, then the oldest
read. A file whose size or time differs from the index is left to the audit (an
edit). A version read before (same size and time) with another SHA-256 is never an
edit: it is listed as damaged, the good digest kept. A first reading compares with
the audit's digests of the same version: the full one when known (a file with a
copy), else the first and last 64 KiB.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.verified_rows import (
    Reading,
    note_damaged,
    note_good,
    oldest_first,
)
from media_hygiene.scan.hashing import full_digest, partial_digest

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.index.verified_rows import Known
    from media_hygiene.services.runtime import Runtime

GB: Final = 1_000_000_000
# A good content known by its first and last 64 KiB only: no copy can be proven.
PARTIAL: Final = "partial:"


@dataclass(frozen=True, slots=True)
class RereadResult:
    """What one run read, and what it found."""

    files: int
    bytes_read: int
    damaged: tuple[str, ...]  # found damaged by this run


def today() -> str:
    """The moment written in the index, in UTC.

    Returns:
        It, ISO 8601 to the second.
    """
    return datetime.now(UTC).isoformat(timespec="seconds")


def reread(runtime: Runtime, budget: int | None = None) -> RereadResult:
    """Read again the files read longest ago, until the budget is spent.

    Args:
        runtime: Settings and mount points.
        budget: Bytes to read; None: `[routine] reread_gb`.

    Returns:
        What was read and found.
    """
    if budget is None:
        budget = int(runtime.settings.routine.reread_gb * GB)
    files, used, damaged = 0, 0, []
    index = runtime.index_file
    if index is None or not index.is_file():
        return RereadResult(0, 0, ())
    with FactsRepository.open(index) as repository:
        connection = repository.connection
        for known in oldest_first(connection):
            if used >= budget:
                break
            read = _read_one(connection, known)
            if read is None:
                continue
            files, used = files + 1, used + known.size
            if read:
                damaged.append(known.path)
            connection.commit()
    return RereadResult(files, used, tuple(damaged))


def _read_one(connection: sqlite3.Connection, known: Known) -> bool | None:
    """Read one file in full and note what it holds.

    Args:
        connection: The index.
        known: What the index knows of it.

    Returns:
        True when found damaged, False when fine, None when not read (gone,
        unreadable, or changed since the audit).
    """
    path = Path(known.path)
    try:
        stat = path.stat()
        if (stat.st_size, stat.st_mtime_ns) != (known.size, known.mtime_ns):
            return None
        digest = full_digest(path)
        good = _good_digest(known, path, digest)
    except OSError:
        return None
    reading = Reading(known.path, (known.size, known.mtime_ns), good, today())
    if good == digest:
        note_good(connection, reading)
        return False
    note_damaged(connection, reading, digest)
    return True


def _good_digest(known: Known, path: Path, digest: str) -> str:
    """The SHA-256 this version of the file should have, when known.

    Args:
        known: What the index knows.
        path: The file.
        digest: Its SHA-256 read now.

    Returns:
        The digest read before of the same version; else the audit's full one; the
        one read now when the audit's partial one matches (or is unknown); else
        `PARTIAL` and the audit's partial digest: damaged, its good SHA-256 unknown.

    Raises:
        OSError: The file cannot be read.
    """
    if known.read is not None and known.read[:2] == (known.size, known.mtime_ns):
        return known.read[2]
    if known.full is not None:
        return known.full
    if known.partial is not None and partial_digest(path) != known.partial:
        return PARTIAL + known.partial
    return digest
