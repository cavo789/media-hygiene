"""When the folders were last walked, read without changing the index file."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.index.schema import MARK_WALKED, WALKED_AT

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.repository import FactsRepository

_LAST_WALK: Final = "SELECT MAX(walked_at) FROM roots"


def last_walk(index_file: Path | None) -> datetime | None:
    """Tell when an audit last walked a folder without a read error.

    The file is opened read-only: no upgrade, no journal file, even on a `:ro` cache.

    Args:
        index_file: The index, None when the cache is not mounted.

    Returns:
        When, or None when unknown (no index, an index without walks, unreadable).
    """
    if index_file is None or not index_file.is_file():
        return None
    try:
        with closing(connect_read_only(index_file)) as connection:
            row = connection.execute(_LAST_WALK).fetchone()
    except sqlite3.Error:
        return None
    return datetime.fromisoformat(row[0]) if row and row[0] else None


def mark_walked(repository: FactsRepository, folder: Path, when: datetime) -> None:
    """Record that a folder was just walked without any read error.

    Args:
        repository: The index, open for writing.
        folder: A mounted folder (container path).
        when: When the walk ended.
    """
    repository.connection.execute(MARK_WALKED, (str(folder), when.isoformat()))


def walked_at(repository: FactsRepository, folder: Path) -> datetime | None:
    """Tell when a folder was last walked without any read error.

    Args:
        repository: The index.
        folder: A mounted folder (container path).

    Returns:
        When, or None when never.
    """
    row = repository.connection.execute(WALKED_AT, (str(folder),)).fetchone()
    return datetime.fromisoformat(row[0]) if row is not None else None
