"""Where each located file of the index was taken, without building its inputs.

The library's places asked `indexed_inputs` for its positions: every file's
classify input, and one Takeout query per file. 4.5 s for 281 positions on the
maintainer's PC (measured, slow log, 2026-11-16). The positions alone need one
pass over the index and one query for every Takeout `.json`; the rule is
`with_takeout`'s: the file's own position, else its `.json`'s, never 0, 0.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.geo.distance import Point
from media_hygiene.index.listing import indexed_files
from media_hygiene.index.takeout_rows import takeout_facts

if TYPE_CHECKING:
    import sqlite3
    from pathlib import Path


def indexed_points(connection: sqlite3.Connection) -> dict[Path, Point]:
    """The position of each located file: its GPS, or its Takeout `.json`'s.

    Args:
        connection: The open index.

    Returns:
        The positions, by container path.
    """
    takeouts = takeout_facts(connection)
    points: dict[Path, Point] = {}
    for file in indexed_files(connection):
        metadata = file.facts.metadata
        point = located_point(metadata)
        takeout = takeouts.get(file.path)
        own = metadata is not None and metadata.located
        if not own and takeout is not None and takeout.located:
            point = _takeout_point(takeout.latitude, takeout.longitude)
        if point is not None:
            points[file.path] = point
    return points


def _takeout_point(latitude: float | None, longitude: float | None) -> Point | None:
    """A Takeout position, as `located_point` reads one.

    Args:
        latitude: Its latitude.
        longitude: Its longitude.

    Returns:
        The point; None at 0, 0 (no fix) or when one is missing.
    """
    if latitude is None or longitude is None or latitude == longitude == 0:
        return None
    return Point(latitude, longitude)
