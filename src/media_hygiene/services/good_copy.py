"""Where a good copy of a damaged file is: a duplicate, a backup, the quarantine (0690).

A candidate is a file of the index (a photo folder or a backup) with the good SHA-256
as its audit's or re-read digest, unchanged since and not damaged itself, then a file
of the quarantine whose journal recorded that SHA-256. Each one is proven by reading
it in full before it is offered: nothing is restored from a copy merely said good.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.errors import JournalError
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.verified_rows import damaged_files
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterator

    from media_hygiene.index.verified_rows import Damaged
    from media_hygiene.services.runtime import Runtime

_TWINS: Final = (
    "SELECT path, size, mtime_ns FROM files WHERE full_digest = ? AND path != ?"
    " UNION SELECT path, size, mtime_ns FROM verified WHERE digest = ? AND path != ?"
    " AND damaged_since IS NULL"
)
_HURT: Final = "SELECT 1 FROM verified WHERE path = ? AND damaged_since IS NOT NULL"


class CopyPlace(StrEnum):
    """Where the good copy lies."""

    LIBRARY = "library"  # a duplicate, in a photo or backup folder
    QUARANTINE = "quarantine"


@dataclass(frozen=True, slots=True)
class Repairable:
    """A damaged file and its good copy, proven; `copy` None: none found."""

    damaged: Damaged
    copy: Path | None
    place: CopyPlace | None


def repairables(runtime: Runtime) -> list[Repairable]:
    """Every damaged file of the index, with a good copy when one is proven.

    Args:
        runtime: Settings and mount points.

    Returns:
        Them, by path.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return []
    with FactsRepository.open(index) as repository:
        connection = repository.connection
        found = [
            (row, list(_library(connection, row))) for row in damaged_files(connection)
        ]
    return [_first(runtime, row, candidates) for row, candidates in found]


def _first(runtime: Runtime, row: Damaged, candidates: list[Path]) -> Repairable:
    """The first candidate whose content proves good.

    Args:
        runtime: Mount points.
        row: The damaged file.
        candidates: Its duplicates in the index.

    Returns:
        It, with its copy (or none).
    """
    for path in candidates:
        if _proven(path, row.digest):
            return Repairable(row, path, CopyPlace.LIBRARY)
    for path in _quarantined(runtime, row.digest):
        if _proven(path, row.digest):
            return Repairable(row, path, CopyPlace.QUARANTINE)
    return Repairable(row, None, None)


def _library(connection: sqlite3.Connection, row: Damaged) -> Iterator[Path]:
    """The files of the index said to hold the good content, unchanged since.

    Args:
        connection: The index.
        row: The damaged file.

    Yields:
        Each one.
    """
    twins = connection.execute(_TWINS, (row.digest, row.path) * 2).fetchall()
    for path, size, mtime in sorted(set(twins)):
        if connection.execute(_HURT, (path,)).fetchone() is not None:
            continue
        try:
            stat = Path(path).stat()
        except OSError:
            continue
        if (stat.st_size, stat.st_mtime_ns) == (size, mtime):
            yield Path(path)


def _quarantined(runtime: Runtime, digest: str) -> Iterator[Path]:
    """The files of the quarantine whose journal recorded this SHA-256.

    Args:
        runtime: Mount points.
        digest: The good SHA-256.

    Yields:
        Each one still there.
    """
    journal_dir = runtime.locations.journal_dir
    for run in list_run_ids(journal_dir):
        try:
            entries = read_journal(journal_file(journal_dir, run))
        except JournalError:
            continue
        for entry in entries:
            if entry.sha256 == digest and entry.quarantine:
                place = Path(entry.quarantine)
                if place.is_file():
                    yield place


def _proven(path: Path, digest: str) -> bool:
    """Read a candidate in full.

    Args:
        path: The candidate.
        digest: The good SHA-256.

    Returns:
        True when it holds that content.
    """
    try:
        return full_digest(path) == digest
    except OSError:
        return False
