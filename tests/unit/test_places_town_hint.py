"""A place named like a town within `[places] town_hint_km`: the hint (0239)."""

from __future__ import annotations

from media_hygiene.config.places_settings import TOWN_HINT_KM
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.geo.point import Point
from media_hygiene.places.town_hint import TownHints

BLANKENBERGE = Point(51.313, 3.132)


def test_the_town_of_that_name_nearby_is_found_folded() -> None:
    """Case, accents and separators do not matter."""
    hints = TownHints(Gazetteer.load(), TOWN_HINT_KM)

    assert hints.of("Blankenberge", BLANKENBERGE) == "Blankenberge"
    assert hints.of("  blankenberge", Point(51.35, 3.2)) == "Blankenberge"


def test_no_hint_for_another_name_a_far_town_or_an_empty_name() -> None:
    """A nickname, a town of that name on another continent, nothing typed."""
    hints = TownHints(Gazetteer.load(), TOWN_HINT_KM)

    assert hints.of("Geer chez papy", BLANKENBERGE) == ""
    assert hints.of("Blankenberge", Point(-33.9, 151.2)) == ""
    assert hints.of("Paris", Point(-33.9, 151.2)) == ""
    assert hints.of("  ", BLANKENBERGE) == ""


def test_the_reach_comes_from_the_setting() -> None:
    """About 6 km from Blankenberge: a hint at 10 km, none at 5 km."""
    towns = Gazetteer.load()
    six_km_away = Point(51.35, 3.2)

    assert (
        TownHints(towns, TOWN_HINT_KM).of("Blankenberge", six_km_away) == "Blankenberge"
    )
    assert TownHints(towns, 5).of("Blankenberge", six_km_away) == ""


def test_the_state_marks_the_places_that_duplicate_a_town() -> None:
    """Each saved place carries `town`, "" when it duplicates none."""
    hints = TownHints(Gazetteer.load(), TOWN_HINT_KM)
    state: dict[str, object] = {
        "places": [
            {"name": "Blankenberge", "latitude": 51.313, "longitude": 3.132},
            {"name": "Maison", "latitude": 51.313, "longitude": 3.132},
        ]
    }

    places = hints.mark(state)["places"]

    assert isinstance(places, list)
    assert [place["town"] for place in places] == ["Blankenberge", ""]
