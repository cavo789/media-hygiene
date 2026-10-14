"""Areas: polygons with holes, possibly several (a multipolygon), and what lies inside.

A point is inside when a ray from it crosses the area's outline an odd number of
times (even-odd rule): an outer ring and its holes, and the separate parts of a
multipolygon, are handled by the same count over every edge. Positions are
`(latitude, longitude)` pairs, in the order of the rest of `config.toml` (GeoJSON
writes them the other way round). An area crossing the 180th meridian is not supported.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.geo.shapes import (
    MAX_POINTS,
    MIN_RING,
    Polygon,
    Position,
    Ring,
    Shape,
    check_shape,
    rings,
)

if TYPE_CHECKING:
    import numpy.typing as npt

    from media_hygiene.geo.distance import Point

__all__ = [
    "MAX_POINTS",
    "MIN_RING",
    "Area",
    "Bounds",
    "Polygon",
    "Position",
    "Ring",
    "Shape",
    "check_shape",
]

_ODD: Final = 2


@dataclass(frozen=True, slots=True)
class Bounds:
    """The box around an area, in degrees."""

    south: float
    west: float
    north: float
    east: float

    def holds(self, point: Point) -> bool:
        """Tell whether a point lies in the box.

        Args:
            point: The point.

        Returns:
            True inside the box or on its edge.
        """
        return (
            self.south <= point.latitude <= self.north
            and self.west <= point.longitude <= self.east
        )

    @property
    def size(self) -> float:
        """The box's surface, in square degrees: the smaller of two areas wins.

        Returns:
            It.
        """
        return (self.north - self.south) * (self.east - self.west)


@dataclass(frozen=True, slots=True)
class Area:
    """An area ready for many point tests: its box and every edge, as arrays."""

    shape: Shape
    bounds: Bounds = field(compare=False)
    edges: npt.NDArray[np.float64] = field(compare=False, repr=False)

    @classmethod
    def of(cls, shape: Shape) -> Area:
        """Prepare an area.

        Args:
            shape: Its polygons, checked by `check_shape`.

        Returns:
            The area.
        """
        rows = [
            (*first, *second)
            for ring in rings(shape)
            for first, second in zip(ring, (*ring[1:], ring[0]), strict=True)
            if first != second
        ]
        points = [position for ring in rings(shape) for position in ring]
        latitudes = [position[0] for position in points]
        longitudes = [position[1] for position in points]
        south, north = min(latitudes), max(latitudes)
        bounds = Bounds(south, min(longitudes), north, max(longitudes))
        return cls(shape, bounds, np.array(rows, dtype=np.float64))

    def contains(self, point: Point) -> bool:
        """Tell whether a point lies inside: in a part, not in one of its holes.

        Args:
            point: The point.

        Returns:
            True inside.
        """
        if not self.bounds.holds(point):
            return False
        lat1, lon1, lat2, lon2 = self.edges.T
        latitude, longitude = point.latitude, point.longitude
        straddles = (lat1 > latitude) != (lat2 > latitude)
        slope = np.divide(
            lon2 - lon1,
            lat2 - lat1,
            out=np.zeros_like(lon1),
            where=straddles,
        )
        crossing = lon1 + slope * (latitude - lat1)
        crossings = int(np.count_nonzero(straddles & (longitude < crossing)))
        return crossings % _ODD == 1
