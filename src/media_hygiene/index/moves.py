"""Where the files the index followed went: old path → new path (version 11).

`config.toml` names a face by its photo's path (`people.naming.face_id`). When `sort`
or `undo` moves a photo, the index moves its rows, and records the move here: a name
confirmed before the move still finds its face (`people.followed`). A path that is
occupied again is no longer "moved away": its row is dropped, so `sort` then `undo`
leaves no loop.
"""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

CREATE_MOVES: Final = """
CREATE TABLE IF NOT EXISTS moves (
    old TEXT PRIMARY KEY,
    new TEXT NOT NULL
)
"""
_FREED: Final = "DELETE FROM moves WHERE old = ?"
_RECORD: Final = "INSERT OR REPLACE INTO moves (old, new) VALUES (?, ?)"
_EVERY: Final = "SELECT old, new FROM moves"


def record_moves(
    connection: sqlite3.Connection, pairs: Sequence[tuple[str, str]]
) -> None:
    """Keep each move, in the transaction that moves the rows.

    Args:
        connection: The index.
        pairs: Old and new path of each file.
    """
    connection.executemany(_FREED, [(new,) for _old, new in pairs])
    connection.executemany(_RECORD, [(old, new) for old, new in pairs if old != new])


def load_moves(connection: sqlite3.Connection) -> dict[str, str]:
    """Every move recorded.

    Args:
        connection: The index (read-only is enough).

    Returns:
        New path by old path; none with an index older than version 11.
    """
    try:
        return dict(connection.execute(_EVERY).fetchall())
    except sqlite3.OperationalError:  # an index read-only, older than the table
        return {}
