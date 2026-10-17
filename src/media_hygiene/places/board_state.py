"""What the map page shows, as JSON: the places, the clusters, those set aside.

A cluster's numbers leave out its photos given a place by hand (0237): all given, it
counts none and leaves the list. A cluster in a circle set aside (0234) carries that
circle's rank: the page hides it, and lists the circle in its "Set aside" fold with
what it holds.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.places.clusters import named
from media_hygiene.places.config_aside import aside_of

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.config.places_settings import IgnoredSpot
    from media_hygiene.places.clusters import Cluster
    from media_hygiene.places.hand_desk import HandDesk

NOT_ASIDE = -1


@dataclass(frozen=True, slots=True)
class BoardView:
    """The board as read back: clusters, places, circles set aside, photos given."""

    clusters: Sequence[Cluster]
    places: Sequence[PersonalPlace]
    aside: Sequence[IgnoredSpot]
    hand: HandDesk


def board_state(view: BoardView) -> dict[str, object]:
    """Describe the board for the page.

    Args:
        view: The board.

    Returns:
        The places (with their rank in the file and their photos given by hand);
        the clusters as `[latitude, longitude, pictures, videos, place, aside]`;
        the circles set aside, with the pictures and videos of their clusters and
        the rank of the largest one (-1: none).
    """
    held = [[0, 0, NOT_ASIDE] for _ in view.aside]
    clusters: list[tuple[float, float, int, int, str, int]] = []
    for rank, item in enumerate(named(view.clusters, view.places)):
        point = item.cluster.point
        pictures, videos = _left(item.cluster, view.hand.given)
        aside = aside_of(point, view.aside)
        if aside is not None and pictures + videos:
            counts = held[aside]
            counts[0] += pictures
            counts[1] += videos
            counts[2] = rank if counts[2] == NOT_ASIDE else counts[2]
        found = (point.latitude, point.longitude, pictures, videos, item.place)
        clusters.append((*found, NOT_ASIDE if aside is None else aside))
    return {
        "places": [
            {"key": key, **place.model_dump(), "hand": view.hand.listed(place.name)}
            for key, place in enumerate(view.places)
        ],
        "clusters": clusters,
        "aside": [
            {
                "key": key,
                "latitude": spot.latitude,
                "longitude": spot.longitude,
                "radius_m": spot.radius_m,
                "pictures": counts[0],
                "videos": counts[1],
                "cluster": counts[2],
            }
            for key, (spot, counts) in enumerate(zip(view.aside, held, strict=True))
        ],
    }


def _left(cluster: Cluster, given: Mapping[Path, str]) -> tuple[int, int]:
    """A cluster's pictures and videos, but those given a place by hand.

    Args:
        cluster: The cluster.
        given: The files given a place.

    Returns:
        Its pictures and videos left.
    """
    if not given:
        return cluster.pictures, cluster.videos
    gone = [file for file in cluster.files if file.path in given]
    videos = sum(file.kind is MediaKind.VIDEO for file in gone)
    return cluster.pictures - (len(gone) - videos), cluster.videos - videos
