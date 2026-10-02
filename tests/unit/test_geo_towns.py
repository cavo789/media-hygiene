"""The GeoNames towns, offline: the snapshot, the nearest town, the largest around."""

from __future__ import annotations

import lzma
from typing import TYPE_CHECKING

import numpy as np
import pytest

from media_hygiene.constants import Locale
from media_hygiene.errors import GeoDataError
from media_hygiene.geo.distance import Point, centre, distance_km
from media_hygiene.geo.gazetteer import GEO_DATA, TOWNS_FILE, Gazetteer
from media_hygiene.geo.nearest import NearestIndex
from media_hygiene.i18n import using
from tests.support.towns import write_towns

if TYPE_CHECKING:
    from pathlib import Path


@pytest.fixture(name="towns")
def towns_fixture(tmp_path: Path) -> Gazetteer:
    """The tiny snapshot."""
    return Gazetteer.load(write_towns(tmp_path))


def test_the_snapshot_keeps_towns_not_their_districts(towns: Gazetteer) -> None:
    """A section of a town (PPLX) is not a town of its own."""
    assert "Turin" in towns.names
    assert "Turin 04 Old district" not in towns.names


def test_the_nearest_town_with_its_region_and_country(towns: Gazetteer) -> None:
    """A position in the old town of Turin."""
    town = towns.nearest(Point(45.0712, 7.6850))
    assert town is not None
    assert (town.name, town.region, town.country) == ("Turin", "Piedmont", "Italy")
    assert town.population_k == 847


def test_country_names_follow_the_language_in_use(towns: Gazetteer) -> None:
    """Written in French when the snapshot was made, never translated at runtime."""
    with using(Locale.FR):
        town = towns.nearest(Point(50.85, 4.35))
    assert town is not None
    assert town.country == "Belgique"


def test_a_suburb_is_named_after_its_large_town(towns: Gazetteer) -> None:
    """The Rocks is nearer, Sydney larger and close by."""
    hotel = Point(-33.8590, 151.2080)
    nearest, main = towns.nearest(hotel), towns.main_town(hotel, 10)
    assert nearest is not None
    assert main is not None
    assert (nearest.name, main.name) == ("The Rocks", "Sydney")


def test_far_from_every_town_the_nearest_still_answers(towns: Gazetteer) -> None:
    """In the middle of the Atlantic: no town in the ring, every town compared."""
    town = towns.main_town(Point(40.0, -30.0), 10)
    assert town is not None
    assert town.name in {"Bruges", "Brussels"}


def test_the_search_ignores_case_and_accents(towns: Gazetteer) -> None:
    """The largest town first; nothing typed, nothing found."""
    assert [town.name for town in towns.search("TUR", 5)] == ["Turin"]
    assert [town.name for town in towns.search("m", 2)] == ["Milan", "Moncalieri"]
    assert towns.search("  ", 5) == ()


def test_a_damaged_snapshot_is_a_clear_error(tmp_path: Path) -> None:
    """No stack trace: a message naming the problem."""
    data = write_towns(tmp_path)
    (data / TOWNS_FILE).write_bytes(lzma.compress(b"Turin\t45\n"))
    with pytest.raises(GeoDataError):
        Gazetteer.load(data)
    (data / TOWNS_FILE).unlink()
    with pytest.raises(GeoDataError):
        Gazetteer.load(data)


def test_the_shipped_snapshot_reads() -> None:
    """The real snapshot: Brussels is in Brussels."""
    town = Gazetteer.load(GEO_DATA).main_town(Point(50.8467, 4.3525), 10)
    assert town is not None
    assert (town.name, town.country) == ("Brussels", "Belgium")


def test_an_empty_index_has_no_nearest_point() -> None:
    """No town at all."""
    empty = NearestIndex(np.array([]), np.array([]))
    assert empty.nearest(Point(0, 0)) is None


def test_the_ring_wraps_around_the_antimeridian() -> None:
    """Fiji, just east of 180°: its neighbour lies just west of it."""
    index = NearestIndex(np.array([-17.0, 10.0]), np.array([179.9, 0.0]))
    found = index.nearest(Point(-17.0, -179.9))
    assert found is not None
    assert found[0] == 0
    assert found[1] < 25


def test_a_wide_search_compares_every_point() -> None:
    """A radius wider than the ring of cells."""
    index = NearestIndex(np.array([50.0, 52.5, 10.0]), np.array([4.0, 4.0, 4.0]))
    assert sorted(index.within(Point(50.0, 4.0), 500).tolist()) == [0, 1]


def test_distances_and_the_middle_of_points() -> None:
    """One degree of latitude is about 111 km; the median resists one outlier."""
    assert distance_km(Point(50, 4), Point(51, 4)) == pytest.approx(111.2, abs=0.1)
    middle = centre([Point(45, 7), Point(45.1, 7.1), Point(50.8, 4.3)])
    assert middle == Point(45.1, 7)
