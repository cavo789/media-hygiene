"""A place named like a town within 10 km: the hint (0239)."""

from __future__ import annotations

from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.geo.point import Point
from media_hygiene.places.town_hint import TownHints, town_nearby

BLANKENBERGE = Point(51.313, 3.132)


def test_the_town_of_that_name_nearby_is_found_folded() -> None:
    """Case, accents and separators do not matter."""
    towns = Gazetteer.load()

    assert town_nearby(towns, "Blankenberge", BLANKENBERGE) == "Blankenberge"
    assert town_nearby(towns, "  blankenberge", Point(51.35, 3.2)) == "Blankenberge"


def test_no_hint_for_another_name_a_far_town_or_an_empty_name() -> None:
    """A nickname, a town of that name on another continent, nothing typed."""
    towns = Gazetteer.load()

    assert town_nearby(towns, "Geer chez papy", BLANKENBERGE) == ""
    assert town_nearby(towns, "Blankenberge", Point(-33.9, 151.2)) == ""
    assert town_nearby(towns, "Paris", Point(-33.9, 151.2)) == ""
    assert town_nearby(towns, "  ", BLANKENBERGE) == ""


def test_the_state_marks_the_places_that_duplicate_a_town() -> None:
    """Each saved place carries `town`, "" when it duplicates none."""
    hints = TownHints(Gazetteer.load())
    state: dict[str, object] = {
        "places": [
            {"name": "Blankenberge", "latitude": 51.313, "longitude": 3.132},
            {"name": "Maison", "latitude": 51.313, "longitude": 3.132},
        ]
    }

    places = hints.mark(state)["places"]

    assert isinstance(places, list)
    assert [place["town"] for place in places] == ["Blankenberge", ""]
