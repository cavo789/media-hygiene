"""The landmark the user named or rejected, cached in `spots` (0649).

The sidecar holds the truth (`tags.xmp_landmark`); this row only lets the search and the
pages find it before the next audit. The row keeps its position and town; its `stamp`
is emptied, so the next audit writes its words again around the new name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.index.spot_rows import SpotSource

if TYPE_CHECKING:
    import sqlite3

_UPDATE: Final = (
    "UPDATE spots SET landmark = ?, source = ?, stamp = '',"
    " words = trim(? || ' ' || words) WHERE path = ?"
)
_INSERT: Final = (
    "INSERT INTO spots (path, latitude, longitude, stamp, landmark, source, town,"
    " region, district, country, words) SELECT path, latitude, longitude, '', ?, ?,"
    " '', '', '', '', ? FROM files WHERE path = ? AND latitude IS NOT NULL"
    " AND longitude IS NOT NULL"
)


def give_landmark(connection: sqlite3.Connection, path: str, name: str) -> None:
    """Cache the user's name (empty: none, by choice) for one file, and commit.

    Args:
        connection: The index, open for writing.
        path: The file, as the index names it.
        name: The landmark.
    """
    source = SpotSource.USER.value
    done = connection.execute(_UPDATE, (name, source, name, path))
    if not done.rowcount:
        connection.execute(_INSERT, (name, source, name, path))
    connection.commit()
