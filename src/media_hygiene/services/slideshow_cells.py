"""The one-degree cells around the located photos of the index (0479)."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING, Final

from media_hygiene.geo.distance import Point
from media_hygiene.geo.landmarks import near_cells
from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from media_hygiene.geo.landmarks import Cells
    from media_hygiene.services.runtime import Runtime

# Truncated, not floored: `near_cells` adds the cells around, which covers the gap.
_LOCATED: Final = (
    "SELECT DISTINCT CAST(json_extract(metadata, '$.latitude') AS INTEGER),"
    " CAST(json_extract(metadata, '$.longitude') AS INTEGER) FROM files"
    " WHERE json_extract(metadata, '$.latitude') IS NOT NULL"
)


def indexed_cells(runtime: Runtime) -> Cells:
    """The cells around the photos of the index that have GPS.

    Args:
        runtime: Where the index lies.

    Returns:
        The cells; none without a kept index.
    """
    index_file = runtime.index_file
    if index_file is None or not index_file.is_file():
        return frozenset()
    try:
        connection = connect_read_only(index_file)
        try:
            rows = connection.execute(_LOCATED).fetchall()
        finally:
            connection.close()
    except sqlite3.Error:
        return frozenset()
    return near_cells(Point(float(lat), float(lon)) for lat, lon in rows)
