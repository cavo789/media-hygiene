"""Areas: inside, outside, in a hole, in a multipolygon's part; which place wins."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.geo.areas import MAX_POINTS, Area, check_shape
from media_hygiene.geo.distance import Point

if TYPE_CHECKING:
    from media_hygiene.geo.areas import Polygon, Shape

# A fictitious village: a diamond, so that its box's corners lie outside it.
DIAMOND: Final[Polygon] = (((50.0, 5.0), (50.1, 5.1), (50.0, 5.2), (49.9, 5.1)),)
HOLED: Final[Polygon] = (
    ((50.0, 5.0), (50.0, 5.4), (50.4, 5.4), (50.4, 5.0), (50.0, 5.0)),
    ((50.1, 5.1), (50.1, 5.2), (50.2, 5.2), (50.2, 5.1)),
)
TWO_PARTS: Final[Shape] = (
    (((10.0, 10.0), (10.0, 11.0), (11.0, 11.0), (11.0, 10.0)),),
    (((12.0, 10.0), (12.0, 11.0), (13.0, 11.0), (13.0, 10.0)),),
)


@pytest.mark.parametrize(
    ("point", "inside"),
    [
        (Point(50.0, 5.1), True),  # the middle
        (Point(50.09, 5.02), False),  # the box's corner, outside the diamond
        (Point(50.2, 5.1), False),  # outside the box
        (Point(50.0, 5.19), True),  # near the east tip
    ],
)
def test_a_diamond(point: Point, inside: bool) -> None:  # noqa: FBT001 - parametrized
    """Inside its outline, not merely inside its box."""
    assert Area.of((DIAMOND,)).contains(point) is inside


@pytest.mark.parametrize(
    ("point", "inside"),
    [(Point(50.05, 5.05), True), (Point(50.15, 5.15), False), (Point(50.3, 5.3), True)],
)
def test_a_hole_is_outside(point: Point, inside: bool) -> None:  # noqa: FBT001
    """A lake in the village is not the village."""
    assert Area.of((HOLED,)).contains(point) is inside


@pytest.mark.parametrize(
    ("point", "inside"),
    [(Point(10.5, 10.5), True), (Point(12.5, 10.5), True), (Point(11.5, 10.5), False)],
)
def test_a_multipolygon(point: Point, inside: bool) -> None:  # noqa: FBT001
    """Two parts: inside either; the gap between them is outside."""
    assert Area.of(TWO_PARTS).contains(point) is inside


@pytest.mark.parametrize(
    "shape",
    [
        (),
        ((),),
        ((((1.0, 1.0), (2.0, 2.0), (1.0, 1.0)),),),
        ((((1.0, 1.0), (2.0, 2.0), (95.0, 1.0)),),),
        ((tuple((float(index), 0.0) for index in range(MAX_POINTS + 1)),),),
    ],
)
def test_impossible_areas_are_refused(shape: Shape) -> None:
    """No polygon, a ring of two points, off the Earth, too detailed."""
    with pytest.raises(ValueError, match=r"area|ring|Earth"):
        check_shape(shape)


def _village() -> PersonalPlace:
    """The fictitious diamond village, as a personal place."""
    return PersonalPlace(
        name="Village", latitude=50.0, longitude=5.1, osm="R1", area=(DIAMOND,)
    )


def test_a_circle_inside_an_area_wins() -> None:
    """Home inside its village is home; the rest of the village is the village."""
    home = PersonalPlace(name="Home", latitude=50.0, longitude=5.1, radius_m=100)
    zones = zones_of([_village(), home])
    assert place_at(Point(50.0, 5.1), zones) == home
    assert place_at(Point(50.0, 5.15), zones) == _village()
    assert place_at(Point(50.09, 5.02), zones) is None


def test_the_smaller_area_wins() -> None:
    """A park inside the village goes to the park."""
    park_ring = ((50.0, 5.09), (50.01, 5.09), (50.01, 5.11), (50.0, 5.11))
    park = PersonalPlace(
        name="Park", latitude=50.0, longitude=5.1, area=((park_ring,),)
    )
    zones = zones_of([_village(), park])
    assert place_at(Point(50.005, 5.1), zones) == park


def test_an_osm_id_names_a_node_a_way_or_a_relation() -> None:
    """`R123`, `W123`, `N123` or nothing."""
    with pytest.raises(ValueError, match="osm"):
        PersonalPlace(name="X", latitude=0.1, longitude=0.1, osm="Q12")
