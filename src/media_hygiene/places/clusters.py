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
MEMBERS_KEPT: Final = 24  # the pictures (and, apart, the videos) shown per cluster
_DECIMALS: Final = 5
SHOWN: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW})  # a video has no preview


@dataclass(frozen=True, slots=True)
class Located:
    """A file of the index and where it was taken."""

    point: Point
    file: MediaFile


@dataclass(frozen=True, slots=True)
class Cluster:
    """Files taken close together: their middle, their numbers, the first ones (0232).

    `pictures` counts every file that is not a video; `members` keeps at most
    `MEMBERS_KEPT` pictures with a preview and as many videos, listed by name;
    `files` every file, to give them to a place (0237).
    """

    point: Point
    pictures: int
    videos: int = 0
    members: tuple[Located, ...] = ()
    files: tuple[MediaFile, ...] = ()

    @property
    def count(self) -> int:
        """Every file of the cluster, pictures and videos."""
        return self.pictures + self.videos


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
        `MEMBERS_KEPT` pictures and its first `MEMBERS_KEPT` videos.
    """
    sums: defaultdict[tuple[int, int], list[float]] = defaultdict(lambda: [0, 0, 0, 0])
    # Per cell: the pictures kept, then the videos kept.
    members: defaultdict[tuple[int, int], tuple[list[Located], list[Located]]] = (
        defaultdict(lambda: ([], []))
    )
    files: defaultdict[tuple[int, int], list[MediaFile]] = defaultdict(list)
    for item in located:
        point = item.point
        key = (
            math.floor(point.latitude / CELL_DEGREES),
            math.floor(point.longitude / CELL_DEGREES),
        )
        total = sums[key]
        total[0] += point.latitude
        total[1] += point.longitude
        video = item.file.kind is MediaKind.VIDEO
        total[3 if video else 2] += 1
        files[key].append(item.file)
        kept = members[key][1 if video else 0]
        if (video or item.file.kind in SHOWN) and len(kept) < MEMBERS_KEPT:
            kept.append(item)
    found = [
        Cluster(
            Point(
                round(lat / (pictures + videos), _DECIMALS),
                round(lon / (pictures + videos), _DECIMALS),
            ),
            int(pictures),
            int(videos),
            (*members[key][0], *members[key][1]),
            tuple(files[key]),
        )
        for key, (lat, lon, pictures, videos) in sums.items()
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
