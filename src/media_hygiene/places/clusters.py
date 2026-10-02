"""Where the photos were taken, as clusters: cells of about 200 m, counted.

The map shows them as circles sized by count; the largest unnamed ones are listed first,
and home is usually the first. Only counts and cell middles reach the page.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.whereabouts import place_at
from media_hygiene.geo.distance import Point

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from media_hygiene.config.classify_places import PersonalPlace

CELL_DEGREES: Final = 0.002  # about 220 m north-south
MAX_CLUSTERS: Final = 5000  # the largest; the page stays light
_DECIMALS: Final = 5


@dataclass(frozen=True, slots=True)
class Cluster:
    """Photos taken close together: their middle and their number."""

    point: Point
    count: int


@dataclass(frozen=True, slots=True)
class NamedCluster:
    """A cluster, and the personal place it lies in (empty: unnamed)."""

    cluster: Cluster
    place: str


def clusters_of(points: Iterable[Point]) -> tuple[Cluster, ...]:
    """Group positions into cells.

    Args:
        points: The position of each photo.

    Returns:
        The clusters, the largest first, at most `MAX_CLUSTERS`.
    """
    sums: defaultdict[tuple[int, int], list[float]] = defaultdict(lambda: [0, 0, 0])
    for point in points:
        key = (
            math.floor(point.latitude / CELL_DEGREES),
            math.floor(point.longitude / CELL_DEGREES),
        )
        total = sums[key]
        total[0] += point.latitude
        total[1] += point.longitude
        total[2] += 1
    found = [
        Cluster(
            Point(round(lat / count, _DECIMALS), round(lon / count, _DECIMALS)),
            int(count),
        )
        for lat, lon, count in sums.values()
    ]
    found.sort(key=lambda cluster: (-cluster.count, cluster.point.latitude))
    return tuple(found[:MAX_CLUSTERS])


def named(
    clusters: Iterable[Cluster], places: Sequence[PersonalPlace]
) -> tuple[NamedCluster, ...]:
    """Tell which clusters lie in a personal place.

    Args:
        clusters: The clusters.
        places: The user's places.

    Returns:
        Each cluster and its place's name, or an empty name.
    """
    return tuple(
        NamedCluster(cluster, found.name if found else "")
        for cluster in clusters
        for found in (place_at(cluster.point, places),)
    )
