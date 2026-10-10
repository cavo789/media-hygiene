"""When the folders were last walked, read without changing the index file."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from datetime import datetime
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from pathlib import Path

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
    uri = f"{index_file.resolve().as_uri()}?mode=ro"
    try:
        with closing(sqlite3.connect(uri, uri=True)) as connection:
            row = connection.execute(_LAST_WALK).fetchone()
    except sqlite3.Error:
        return None
    return datetime.fromisoformat(row[0]) if row and row[0] else None
