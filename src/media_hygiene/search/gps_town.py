"""The town of a GPS position, for the large view's facts (key I, 0458).

Read from the offline GeoNames snapshot (`geo/`): no position ever leaves the machine.
The snapshot is loaded once, at the first photo with a position.
"""

from __future__ import annotations

from functools import cache

from media_hygiene.errors import GeoDataError
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.geo.point import Point


@cache
def _towns() -> Gazetteer | None:
    """The snapshot, loaded once.

    Returns:
        It, or None when it cannot be read.
    """
    try:
        return Gazetteer.load()
    except GeoDataError:
        return None


def town_text(latitude: float, longitude: float) -> str:
    """Name the town nearest to a position, with its country.

    Args:
        latitude: Degrees north.
        longitude: Degrees east.

    Returns:
        `Brussels, Belgium`, or empty when no town is known.
    """
    towns = _towns()
    town = None if towns is None else towns.nearest(Point(latitude, longitude))
    if town is None:
        return ""
    return f"{town.name}, {town.country}" if town.country else town.name
