"""The nearest of many points, fast: a grid of one-degree cells, then numpy.

A position is compared with the points of its cell and the eight around it. When the
best of them is farther than the ring is wide (at sea, near the poles), every point is
compared: the answer is always the true nearest.
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.geo.distance import KM_PER_DEGREE, distances_km

if TYPE_CHECKING:
    import numpy.typing as npt

    from media_hygiene.geo.distance import Point

_RING: Final = (-1, 0, 1)
_RIGHT_ANGLE: Final = 90.0
_FULL_TURN: Final = 360


class NearestIndex:
    """Answers "which point is nearest?" among a fixed set of points."""

    def __init__(
        self, latitudes: npt.NDArray[np.float64], longitudes: npt.NDArray[np.float64]
    ) -> None:
        """Sort the points into cells.

        Args:
            latitudes: Their latitudes, in degrees.
            longitudes: Their longitudes, in degrees (same length).
        """
        self._latitudes = latitudes
        self._longitudes = longitudes
        cells: defaultdict[tuple[int, int], list[int]] = defaultdict(list)
        for index, (lat, lon) in enumerate(
            zip(latitudes.tolist(), longitudes.tolist(), strict=True)
        ):
            cells[_cell(lat, lon)].append(index)
        self._cells = {key: np.array(found) for key, found in cells.items()}

    def nearest(self, point: Point) -> tuple[int, float] | None:
        """The nearest point.

        Args:
            point: A position.

        Returns:
            Its index and distance in kilometres; None when there is no point at all.
        """
        if not self._latitudes.size:
            return None
        around = self._ring(point)
        if around.size:
            best = self._best(point, around)
            if best[1] <= _ring_width_km(point.latitude):
                return best
        return self._best(point, np.arange(self._latitudes.size))

    def within(self, point: Point, radius_km: float) -> npt.NDArray[np.int_]:
        """The points around a position.

        Args:
            point: A position.
            radius_km: How far around it.

        Returns:
            Their indexes.
        """
        reach = _ring_width_km(point.latitude)
        candidates = (
            self._ring(point) if radius_km <= reach else np.arange(self._latitudes.size)
        )
        distances = distances_km(
            point, self._latitudes[candidates], self._longitudes[candidates]
        )
        return candidates[distances <= radius_km]

    def _ring(self, point: Point) -> npt.NDArray[np.int_]:
        """The points of a position's cell and of the eight around it.

        Args:
            point: A position.

        Returns:
            Their indexes.
        """
        row, column = _cell(point.latitude, point.longitude)
        around = [
            found
            for step in _RING
            for side in _RING
            if (found := self._cells.get((row + step, _wrap(column + side))))
            is not None
        ]
        return np.concatenate(around) if around else np.array([], dtype=np.int_)

    def _best(
        self, point: Point, candidates: npt.NDArray[np.int_]
    ) -> tuple[int, float]:
        """The nearest of some points.

        Args:
            point: A position.
            candidates: The indexes to compare.

        Returns:
            The index of the nearest and its distance.
        """
        distances = distances_km(
            point, self._latitudes[candidates], self._longitudes[candidates]
        )
        best = int(np.argmin(distances))
        return int(candidates[best]), float(distances[best])


def _cell(latitude: float, longitude: float) -> tuple[int, int]:
    """The one-degree cell of a position.

    Args:
        latitude: In degrees.
        longitude: In degrees.

    Returns:
        Its row and column.
    """
    return math.floor(latitude), _wrap(math.floor(longitude))


def _wrap(column: int) -> int:
    """Keep a column in -180..179: east of 179 is -180.

    Args:
        column: A column, maybe one step beyond the antimeridian.

    Returns:
        The same column, wrapped.
    """
    return (column + _FULL_TURN // 2) % _FULL_TURN - _FULL_TURN // 2


def _ring_width_km(latitude: float) -> float:
    """How far around a position the ring of cells surely reaches.

    Args:
        latitude: The position's latitude.

    Returns:
        One cell, east-west, at the ring's latitude farthest from the equator.
    """
    edge = min(abs(latitude) + 1, _RIGHT_ANGLE)
    return KM_PER_DEGREE * math.cos(math.radians(edge))
