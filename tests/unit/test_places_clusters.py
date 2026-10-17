"""The clusters of the `places` map: every positioned photo counted once, in its cell.

TODO 0164: the docs capture shows the Genval lake series as "3 photos" although the
scenario positions 4. The map is right: the burst review sets IMG_4002 aside,
`clean --decisions` quarantines it and `purge` deletes it before the map is shot.
These tests pin that a series of N positions of the scenario is one cluster of N.
"""

from __future__ import annotations

from pathlib import Path

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.geo.distance import Point
from media_hygiene.places.clusters import (
    CELL_DEGREES,
    MEMBERS_KEPT,
    Located,
    clusters_of,
)
from media_hygiene.scan.models import MediaFile
from tests.support.docs.events import GENVAL, PARK, near


def _located(point: Point, name: str, kind: MediaKind = MediaKind.IMAGE) -> Located:
    """A file of the index at a position."""
    return Located(point, MediaFile(Path("/data/c/Photos") / name, 1, 1, kind))


def _series(place: tuple[float, float], steps: range) -> list[Located]:
    """The positions the docs scenario writes into a series of photos."""
    return [_located(Point(*near(place, step)), f"IMG_{step}.jpg") for step in steps]


@pytest.mark.parametrize(
    ("place", "steps"),
    [
        pytest.param(GENVAL, range(4), id="lake-burst-of-4"),
        pytest.param(PARK, range(8), id="birthday-park-8"),
    ],
)
def test_a_scenario_series_is_one_cluster_of_its_size(
    place: tuple[float, float], steps: range
) -> None:
    """The jitter of the scenario never pushes a photo into a neighbouring cell."""
    found = clusters_of(_series(place, steps))

    assert [cluster.count for cluster in found] == [len(steps)]


def test_two_places_give_two_clusters_largest_first() -> None:
    """Each photo is counted once, in the cluster of its own cell."""
    found = clusters_of([*_series(GENVAL, range(4)), *_series(PARK, range(8))])

    assert [cluster.count for cluster in found] == [8, 4]
    assert found[1].point.latitude == pytest.approx(GENVAL[0], abs=CELL_DEGREES)


def test_the_same_position_twice_is_counted_twice() -> None:
    """Two photos at one spot (a burst without jitter) count as two."""
    spot = Point(*GENVAL)
    found = clusters_of([_located(spot, "a.jpg"), _located(spot, "b.jpg")])

    assert [cluster.count for cluster in found] == [2]


def test_a_cluster_keeps_its_first_pictures_then_its_videos() -> None:
    """Pictures and videos counted apart; at most `MEMBERS_KEPT` of each kept."""
    spot = Point(*GENVAL)
    video = _located(spot, "clip.mp4", MediaKind.VIDEO)
    raw = _located(spot, "shot.cr2", MediaKind.RAW)
    many = [_located(spot, f"IMG_{index}.jpg") for index in range(MEMBERS_KEPT + 5)]

    (cluster,) = clusters_of([video, raw, *many])

    assert (cluster.pictures, cluster.videos) == (MEMBERS_KEPT + 6, 1)
    assert cluster.count == MEMBERS_KEPT + 7
    assert len(cluster.members) == MEMBERS_KEPT + 1
    assert cluster.members[0] == raw
    assert cluster.members[-1] == video  # the videos after the pictures


def test_a_cluster_of_one_video_is_no_photo() -> None:
    """TODO 0232: "1 photo", then "0 photos out of 1"; now one video, listed."""
    video = _located(Point(*GENVAL), "clip.mp4", MediaKind.VIDEO)

    (cluster,) = clusters_of([video])

    assert (cluster.pictures, cluster.videos, cluster.count) == (0, 1, 1)
    assert cluster.members == (video,)


def test_the_videos_kept_are_capped_too() -> None:
    """Many videos at one spot: `MEMBERS_KEPT` listed, every one counted."""
    spot = Point(*GENVAL)
    clips = [
        _located(spot, f"clip_{index}.mp4", MediaKind.VIDEO)
        for index in range(MEMBERS_KEPT + 3)
    ]

    (cluster,) = clusters_of([_located(spot, "IMG_1.jpg"), *clips])

    assert (cluster.pictures, cluster.videos) == (1, MEMBERS_KEPT + 3)
    assert len(cluster.members) == MEMBERS_KEPT + 1
