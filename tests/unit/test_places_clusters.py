"""The clusters of the `places` map: every positioned photo counted once, in its cell.

TODO 0164: the docs capture shows the Genval lake series as "3 photos" although the
scenario positions 4. The map is right: the burst review sets IMG_4002 aside,
`clean --decisions` quarantines it and `purge` deletes it before the map is shot.
These tests pin that a series of N positions of the scenario is one cluster of N.
"""

from __future__ import annotations

import pytest

from media_hygiene.geo.distance import Point
from media_hygiene.places.clusters import CELL_DEGREES, clusters_of
from tests.support.docs.events import GENVAL, PARK, near


def _series(place: tuple[float, float], steps: range) -> list[Point]:
    """The positions the docs scenario writes into a series of photos."""
    return [Point(*near(place, step)) for step in steps]


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

    assert [cluster.count for cluster in clusters_of([spot, spot])] == [2]
