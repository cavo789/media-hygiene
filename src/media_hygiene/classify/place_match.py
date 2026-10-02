"""Which personal place a position lies in: within a circle, or inside an area.

The places are prepared once (`zones_of`), then tested against every position. When
several hold a position, a circle wins over an area (home inside its village is
home), the closest circle among circles, the smallest area among areas.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.geo.areas import Area
from media_hygiene.geo.distance import METRES_PER_KM, distance_km

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.geo.distance import Point

type Rank = tuple[int, float]  # (0, metres) in a circle, (1, size) in an area


@dataclass(frozen=True, slots=True)
class Zone:
    """A personal place, its area prepared for point tests (None: a circle)."""

    place: PersonalPlace
    area: Area | None

    def rank(self, point: Point) -> Rank | None:
        """How well the place holds a position: the lower, the better.

        Args:
            point: The position.

        Returns:
            Its rank, or None outside the place.
        """
        if self.area is not None:
            return (1, self.area.bounds.size) if self.area.contains(point) else None
        metres = distance_km(point, self.place.point) * METRES_PER_KM
        return (0, metres) if metres <= self.place.radius_m else None


def zones_of(places: Iterable[PersonalPlace]) -> tuple[Zone, ...]:
    """Prepare the places for many point tests.

    Args:
        places: The user's places.

    Returns:
        One zone per place, in the same order.
    """
    return tuple(
        Zone(place, None if place.area is None else Area.of(place.area))
        for place in places
    )


def place_at(point: Point, zones: Sequence[Zone]) -> PersonalPlace | None:
    """The personal place a position lies in, the best one when several hold it.

    Args:
        point: A position.
        zones: The user's places, prepared.

    Returns:
        The place, or None.
    """
    found = [
        (rank, zone.place) for zone in zones if (rank := zone.rank(point)) is not None
    ]
    return min(found, key=lambda item: item[0])[1] if found else None
