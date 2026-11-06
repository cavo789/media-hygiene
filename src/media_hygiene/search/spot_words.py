"""The full-text table, built with the words of each located photo too (0545).

An index older than `spots`, opened read-only, has no such table yet: it is left out.
"""

from __future__ import annotations

from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.index.spot_rows import CURRENT
from media_hygiene.search import statements as sql
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    import sqlite3

_HAS_SPOTS: Final = (
    "SELECT 1 FROM sqlite_master WHERE type = 'table' AND name = 'spots'"
)
_SPOT_ROWS: Final = (
    "SELECT f.path AS path, f.size AS size, f.mtime_ns AS mtime_ns,"  # noqa: S608
    f" '{TagSource.PLACE.value}' AS source, s.words AS value FROM files AS f {CURRENT}"
)
_BETWEEN: Final = " UNION ALL "


def rebuild(connection: sqlite3.Connection, *, tagged: bool) -> None:
    """Build the full-text table again.

    Args:
        connection: The index.
        tagged: Whether it has a table of tags.
    """
    rows = [sql.TAG_ROWS] if tagged else []
    rows.append(sql.PERSON_ROWS)
    if connection.execute(_HAS_SPOTS).fetchone() is not None:
        rows.append(_SPOT_ROWS)
    with closing(connection.cursor()) as cursor:
        cursor.execute(sql.DROP)
        cursor.execute(sql.CREATE)
        cursor.execute(sql.FILL_ROWS.format(rows=_BETWEEN.join(rows)))
    connection.commit()
