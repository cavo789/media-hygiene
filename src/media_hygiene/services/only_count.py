"""How many files of the quarantine exist nowhere else, for the home: from the index.

`only_copies` asks the disk about every file set aside and every kept twin: through
Docker Desktop, 36,569 checks took 55 s of the home page's 60 s (measured in the
maintainer's `mh home` container, 83 runs and 29,696 files in the quarantine,
2026-11-11). The card only needs a number: here each kept twin is looked up in the
index the audit keeps (one query per batch), and each file set aside is counted from
its journal. A twin deleted since the last audit still counts as there until the next
one; `purge` asks the disk itself before erasing anything (`only_copies`).
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.errors import JournalError
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.services.only_copies import set_aside

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry

_BATCH: Final = 500  # paths per query: under SQLite's limit of bound parameters
_SIZES: Final = "SELECT path, size FROM files WHERE path IN ({marks})"


def only_count(
    index_file: Path | None, journal_dir: Path, runs: Sequence[str]
) -> int | None:
    """Count the files of these runs' quarantines with no kept twin in the index.

    Args:
        index_file: The index; None when the cache is not mounted.
        journal_dir: Journal mount point.
        runs: The runs in the quarantine.

    Returns:
        The count; None without a readable index. A run whose journal is lost is
        left out: the card's way back line names it already.
    """
    if index_file is None or not index_file.is_file():
        return None
    held: list[JournalEntry] = []
    for run in runs:
        try:
            held += set_aside(read_journal_once(journal_file(journal_dir, run)))
        except JournalError, OSError:
            continue
    twins = [(entry, twin) for entry in held if (twin := _twin(entry)) is not None]
    try:
        sizes = _sizes(index_file, sorted({twin for _entry, twin in twins}))
    except sqlite3.Error:
        return None
    covered = sum(sizes.get(twin) == entry.size for entry, twin in twins)
    return len(held) - covered


def _twin(entry: JournalEntry) -> str | None:
    """The kept copy an exact copy was compared with, byte for byte.

    Args:
        entry: A file set aside.

    Returns:
        Its path; None for anything but an exact copy (no other copy).
    """
    if entry.action is not ActionKind.QUARANTINE_DUPLICATE:
        return None
    return entry.keeper


def _sizes(index_file: Path, paths: list[str]) -> dict[str, int]:
    """Read the size the index knows of each path, in batches.

    Args:
        index_file: The index.
        paths: Container paths.

    Returns:
        The size by path, for the paths the index holds.

    Raises:
        sqlite3.Error: The index cannot be read.
    """
    found: dict[str, int] = {}
    with closing(connect_read_only(index_file)) as connection:
        for start in range(0, len(paths), _BATCH):
            batch = paths[start : start + _BATCH]
            query = _SIZES.format(marks=",".join("?" * len(batch)))
            found.update(connection.execute(query, batch).fetchall())
    return found
