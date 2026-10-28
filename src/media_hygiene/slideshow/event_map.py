"""The background of an event's small map on the phone (0449): its frame, its towns.

The frame is the box of the event's positions with a margin; the towns are a handful
of the offline GeoNames snapshot's inside it, spread over it: the nearest town to each
point of a small grid, plus the largest one around the middle. Nothing leaves the
machine; the phone draws them as labels, or under tiles when `[places] tiles` is set.
"""

from __future__ import annotations

from dataclasses import dataclass
from itertools import product
from typing import TYPE_CHECKING, Final

from media_hygiene.geo.distance import distance_km
from media_hygiene.geo.point import Point

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.geo.gazetteer import Gazetteer, Town

# The margin around the photos: a quarter of their span, at least ~2 km.
_MARGIN_SHARE: Final = 0.25
_MIN_MARGIN_DEG: Final = 0.02
_GRID: Final = (0.2, 0.5, 0.8)  # where the towns are looked for, across the frame
MAX_TOWNS: Final = 6  # labels a phone's small map can hold


@dataclass(frozen=True, slots=True)
class EventMap:
    """The frame (south, west, north, east) and the towns drawn in it."""

    frame: tuple[float, float, float, float]
    towns: tuple[Town, ...] = ()

    def view(self) -> dict[str, object]:
        """The map, for the phone.

        Returns:
            The frame and each town's name and position.
        """
        return {
            "frame": list(self.frame),
            "towns": [
                [town.name, town.point.latitude, town.point.longitude]
                for town in self.towns
            ],
        }


def event_map(points: Sequence[Point], gazetteer: Gazetteer | None) -> EventMap | None:
    """The map of an event's positions.

    Args:
        points: The positions of its located photos.
        gazetteer: The towns; None: the frame only.

    Returns:
        The map; None without a position.
    """
    if not points:
        return None
    lats = [point.latitude for point in points]
    lons = [point.longitude for point in points]
    lat_pad = max((max(lats) - min(lats)) * _MARGIN_SHARE, _MIN_MARGIN_DEG)
    lon_pad = max((max(lons) - min(lons)) * _MARGIN_SHARE, _MIN_MARGIN_DEG)
    frame = (
        max(min(lats) - lat_pad, -90.0),
        max(min(lons) - lon_pad, -180.0),
        min(max(lats) + lat_pad, 90.0),
        min(max(lons) + lon_pad, 180.0),
    )
    if gazetteer is None:
        return EventMap(frame)
    return EventMap(frame, _towns_in(frame, gazetteer))


def _towns_in(
    frame: tuple[float, float, float, float], gazetteer: Gazetteer
) -> tuple[Town, ...]:
    """A handful of towns spread over a frame, the largest first.

    Args:
        frame: South, west, north, east.
        gazetteer: The towns.

    Returns:
        At most `MAX_TOWNS` towns inside the frame.
    """
    south, west, north, east = frame
    middle = Point((south + north) / 2, (west + east) / 2)
    found: dict[str, Town] = {}
    radius = distance_km(middle, Point(north, east))
    largest = gazetteer.main_town(middle, radius)
    if largest is not None:
        found[largest.name] = largest
    for across, up in product(_GRID, _GRID):
        spot = Point(south + (north - south) * up, west + (east - west) * across)
        near = gazetteer.nearest(spot)
        if near is not None:
            found.setdefault(near.name, near)
    inside = [
        town
        for town in found.values()
        if south <= town.point.latitude <= north
        and west <= town.point.longitude <= east
    ]
    inside.sort(key=lambda town: -town.population_k)
    return tuple(inside[:MAX_TOWNS])
