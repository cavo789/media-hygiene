"""Where the photos were taken, as clusters: cells of about 200 m, counted.

The map shows them as circles sized by count; the largest unnamed ones are listed first,
and home is usually the first. The state of the page holds only counts and cell middles;
the first photos of each cell are kept for `GET /api/cluster/<rank>` (`photos`), which
shows them to recognise the place before naming it.
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.constants import MediaKind
from media_hygiene.geo.distance import Point

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.scan.models import MediaFile

CELL_DEGREES: Final = 0.002  # about 220 m north-south
MAX_CLUSTERS: Final = 5000  # the largest; the page stays light
MEMBERS_KEPT: Final = 24  # the photos shown per cluster, a grid under the list
_DECIMALS: Final = 5
_SHOWN: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})  # a video has no preview


@dataclass(frozen=True, slots=True)
class Located:
    """A file of the index and where it was taken."""

    point: Point
    file: MediaFile


@dataclass(frozen=True, slots=True)
class Cluster:
    """Photos taken close together: their middle, their number, the first photos."""

    point: Point
    count: int
    members: tuple[Located, ...] = ()  # pictures only, at most `MEMBERS_KEPT`


@dataclass(frozen=True, slots=True)
class NamedCluster:
    """A cluster, and the personal place it lies in (empty: unnamed)."""

    cluster: Cluster
    place: str


def clusters_of(located: Iterable[Located]) -> tuple[Cluster, ...]:
    """Group positions into cells.

    Args:
        located: Each photo and video, and its position.

    Returns:
        The clusters, the largest first, at most `MAX_CLUSTERS`; each keeps its first
        `MEMBERS_KEPT` pictures.
    """
    sums: defaultdict[tuple[int, int], list[float]] = defaultdict(lambda: [0, 0, 0])
    members: defaultdict[tuple[int, int], list[Located]] = defaultdict(list)
    for item in located:
        point = item.point
        key = (
            math.floor(point.latitude / CELL_DEGREES),
            math.floor(point.longitude / CELL_DEGREES),
        )
        total = sums[key]
        total[0] += point.latitude
        total[1] += point.longitude
        total[2] += 1
        kept = members[key]
        if item.file.kind in _SHOWN and len(kept) < MEMBERS_KEPT:
            kept.append(item)
    found = [
        Cluster(
            Point(round(lat / count, _DECIMALS), round(lon / count, _DECIMALS)),
            int(count),
            tuple(members[key]),
        )
        for key, (lat, lon, count) in sums.items()
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
    zones = zones_of(places)
    return tuple(
        NamedCluster(cluster, found.name if found else "")
        for cluster in clusters
        for found in (place_at(cluster.point, zones),)
    )
