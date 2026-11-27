"""Where each located file of the index was taken, without building its inputs.

The library's places asked `indexed_inputs` for its positions: every file's
classify input, and one Takeout query per file (4.5 s for 281 positions on the
maintainer's PC), then every file's facts decoded (3.2 s; measured, slow log,
2026-11-16). The index keeps the position in typed columns: two queries, nothing
decoded. The rule is `with_takeout`'s: the file's own position, else its `.json`'s
when the file holds none, never 0, 0.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.geo.distance import Point

if TYPE_CHECKING:
    import sqlite3

_OWN: Final = (
    "SELECT path, latitude, longitude FROM files"
    " WHERE latitude IS NOT NULL AND longitude IS NOT NULL"
)
_TAKEOUT: Final = (
    "SELECT takeout.path, takeout.latitude, takeout.longitude"
    " FROM takeout JOIN files ON files.path = takeout.path"
    " WHERE (files.latitude IS NULL OR files.longitude IS NULL)"
    " AND takeout.latitude IS NOT NULL AND takeout.longitude IS NOT NULL"
)


def indexed_points(connection: sqlite3.Connection) -> dict[Path, Point]:
    """The position of each located file: its GPS, or its Takeout `.json`'s.

    Args:
        connection: The open index.

    Returns:
        The positions, by container path.
    """
    points: dict[Path, Point] = {}
    for query in (_OWN, _TAKEOUT):
        for path, latitude, longitude in connection.execute(query):
            if not latitude == longitude == 0:  # a receiver without a fix
                points[Path(path)] = Point(float(latitude), float(longitude))
    return points
