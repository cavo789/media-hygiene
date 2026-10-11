"""Count the faces of the index for `status`, without changing the index file."""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from pathlib import Path

_COVERAGE: Final = "SELECT COUNT(*), COALESCE(SUM(faces), 0) FROM face_scans"


def face_coverage(index_file: Path | None) -> tuple[int, int] | None:
    """Count the photos analysed and the faces found, of any model.

    Args:
        index_file: The index, None when the cache is not mounted.

    Returns:
        Photos analysed and faces found; None without an index, an index older than
        the faces, or before any `people` run.
    """
    if index_file is None or not index_file.is_file():
        return None
    try:
        with closing(connect_read_only(index_file)) as connection:
            row = connection.execute(_COVERAGE).fetchone()
    except sqlite3.Error:
        return None
    return (int(row[0]), int(row[1])) if row and row[0] else None
