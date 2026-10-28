"""The storyteller's small map (0449): towns offline, or opt-in tiles."""

from __future__ import annotations

from media_hygiene.config.places_settings import PlacesSettings
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.geo.point import Point
from media_hygiene.services.slideshow_map import map_tiles
from media_hygiene.slideshow.event_map import MAX_TOWNS, event_map

_VALKENBURG = Point(50.865, 5.832)


def test_no_position_no_map() -> None:
    """No located photo: no map."""
    assert event_map([], None) is None


def test_the_frame_holds_the_points_with_a_margin() -> None:
    """The frame holds every point, with a margin."""
    other = Point(50.87, 5.84)
    found = event_map([_VALKENBURG, other], None)
    assert found is not None
    south, west, north, east = found.frame
    assert south < _VALKENBURG.latitude < other.latitude < north
    assert west < _VALKENBURG.longitude < other.longitude < east
    assert not found.towns


def test_the_towns_lie_in_the_frame_largest_first() -> None:
    """A handful of towns inside the frame, the largest first."""
    found = event_map([_VALKENBURG], Gazetteer.load())
    assert found is not None
    assert 0 < len(found.towns) <= MAX_TOWNS
    south, west, north, east = found.frame
    for town in found.towns:
        assert south <= town.point.latitude <= north
        assert west <= town.point.longitude <= east
    sizes = [town.population_k for town in found.towns]
    assert sizes == sorted(sizes, reverse=True)
    view = found.view()
    assert view["frame"] == list(found.frame)
    assert len(view["towns"]) == len(found.towns)  # type: ignore[arg-type]


def test_the_default_tiles_are_not_used_offline_by_default() -> None:
    """The default tiles are never fetched: the map stays offline."""
    tiles = map_tiles(PlacesSettings())
    assert not tiles.url
    assert "tile.openstreetmap.org" not in tiles.policy
    assert tiles.referrer == "no-referrer"


def test_tiles_set_by_the_user_are_allowed_by_the_policy_only_them() -> None:
    """Tiles the user set: their host only, in the policy."""
    url = "https://{s}.tile.example.org/{z}/{x}/{y}.png"
    tiles = map_tiles(PlacesSettings(tiles=url))
    assert tiles.url == url
    assert "img-src 'self' https://*.tile.example.org;" in tiles.policy
    assert "connect-src 'self'" in tiles.policy
    assert tiles.referrer == "strict-origin"
