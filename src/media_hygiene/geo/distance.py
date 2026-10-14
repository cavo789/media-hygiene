"""Points on the Earth and the distances between them, great-circle (haversine).

Accurate to about 0.5 %: plenty to tell a garden from the next town.
"""

from __future__ import annotations

import math
from statistics import median
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.geo.point import Point

if TYPE_CHECKING:
    from collections.abc import Iterable

    import numpy.typing as npt

EARTH_RADIUS_KM: Final = 6371.0088
KM_PER_DEGREE: Final = math.pi * EARTH_RADIUS_KM / 180
METRES_PER_KM: Final = 1000

__all__ = [
    "EARTH_RADIUS_KM",
    "KM_PER_DEGREE",
    "METRES_PER_KM",
    "Point",
    "centre",
    "distance_km",
    "distances_km",
]


def distance_km(first: Point, second: Point) -> float:
    """The great-circle distance between two points.

    Args:
        first: A point.
        second: Another point.

    Returns:
        The distance, in kilometres.
    """
    found = distances_km(
        first, np.array([second.latitude]), np.array([second.longitude])
    )
    return float(found[0])


def distances_km(
    origin: Point,
    latitudes: npt.NDArray[np.float64],
    longitudes: npt.NDArray[np.float64],
) -> npt.NDArray[np.float64]:
    """The great-circle distances from one point to many.

    Args:
        origin: The point.
        latitudes: The latitudes of the others, in degrees.
        longitudes: Their longitudes, in degrees.

    Returns:
        One distance per other point, in kilometres.
    """
    lat1, lon1 = math.radians(origin.latitude), math.radians(origin.longitude)
    lat2, lon2 = np.radians(latitudes), np.radians(longitudes)
    half = (
        np.sin((lat2 - lat1) / 2) ** 2
        + math.cos(lat1) * np.cos(lat2) * np.sin((lon2 - lon1) / 2) ** 2
    )
    arcs: npt.NDArray[np.float64] = np.arcsin(np.sqrt(np.clip(half, 0.0, 1.0)))
    return 2 * EARTH_RADIUS_KM * arcs


def centre(points: Iterable[Point]) -> Point:
    """The middle of a few points: the median latitude and longitude.

    The median, not the mean: one photo geotagged at home in the middle of a trip
    does not drag the trip halfway back.

    Args:
        points: At least one point.

    Returns:
        Their middle.
    """
    listed = tuple(points)
    return Point(
        median(point.latitude for point in listed),
        median(point.longitude for point in listed),
    )
