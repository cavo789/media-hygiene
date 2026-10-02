"""The `trip` rule: events far from home, joined over several days, named offline."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.models import Band, SortReason
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.constants import Locale
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.i18n import using
from tests.support.located import (
    BRUGES,
    HOME,
    MILAN,
    MONCALIERI,
    PLACE_RULE,
    TRIP_RULE,
    TURIN,
    located,
    outing,
    run,
    start_of,
)
from tests.support.towns import write_towns

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput, Proposal

BRUSSELS = (50.8467, 4.3525)  # about 80 km from home: not a trip
AT_HOME = (HOME.latitude, HOME.longitude)
FIVE = 5


@pytest.fixture(name="towns")
def towns_fixture(tmp_path: Path) -> Gazetteer:
    """The tiny snapshot."""
    return Gazetteer.load(write_towns(tmp_path))


def day(
    prefix: str, number: int, where: tuple[float, float] | None
) -> list[MediaInput]:
    """Five photos taken on one day of July 2023, all at one position (or none)."""
    return outing(prefix, start_of(number), (where,) * FIVE)


def categories(found: Mapping[str, Proposal], prefix: str) -> set[str]:
    """The categories of the photos whose name starts so."""
    return {p.category for name, p in found.items() if name.startswith(prefix)}


def test_an_outing_far_from_home_is_a_trip_named_offline(towns: Gazetteer) -> None:
    """`{country}/{city}` by default, sure."""
    found = run(day("t", 1, TURIN), (TRIP_RULE,), towns)
    first = found["t0.jpg"]
    assert (first.band, first.reason, first.rule) == (
        Band.SURE,
        SortReason.TRIP,
        "Trips",
    )
    assert first.folder == "2023/Italy/Turin"


def test_country_names_in_french(towns: Gazetteer) -> None:
    """The language of the interface names the country."""
    with using(Locale.FR):
        found = run(day("t", 1, TURIN), (TRIP_RULE,), towns)
    assert found["t0.jpg"].category == "Italie/Turin"


def test_days_close_in_time_and_space_make_one_trip(towns: Gazetteer) -> None:
    """Turin then Moncalieri the next day: one trip, named after its largest day."""
    photos = [
        *outing("a", start_of(1), (TURIN,) * 6),
        *day("b", 2, MONCALIERI),
    ]
    found = run(photos, (TRIP_RULE,), towns)
    assert categories(found, "") == {"Italy/Turin"}


def test_a_day_without_gps_between_two_days_of_a_trip_joins_it(
    towns: Gazetteer,
) -> None:
    """A camera without GPS on the second day: it inherits, to check."""
    photos = [*day("a", 1, TURIN), *day("b", 2, None), *day("c", 3, MONCALIERI)]
    found = run(photos, (TRIP_RULE,), towns)
    neighbour = found["b0.jpg"]
    assert (neighbour.reason, neighbour.category, neighbour.band) == (
        SortReason.TRIP_NEIGHBOUR,
        "Italy/Turin",
        Band.UNSURE,
    )


def test_a_day_without_gps_after_the_trip_stays_out(towns: Gazetteer) -> None:
    """Back home, the camera without GPS: nothing says it was still the trip."""
    photos = [*day("a", 1, TURIN), *day("b", 2, None)]
    found = run(photos, (TRIP_RULE,), towns)
    assert found["b0.jpg"].reason is not SortReason.TRIP_NEIGHBOUR


def test_too_far_apart_or_too_long_apart_makes_two_trips(towns: Gazetteer) -> None:
    """Milan is 126 km from Turin; four days later is another trip.

    Moncalieri lies 8 km from Turin, a much larger town: the trip is named Turin.
    """
    photos = [
        *day("a", 1, TURIN),
        *day("b", 2, MILAN),
        *day("x", 6, None),
        *day("c", 7, MONCALIERI),
    ]
    found = run(photos, (TRIP_RULE,), towns)
    assert categories(found, "a") == {"Italy/Turin"}
    assert categories(found, "b") == {"Italy/Milan"}
    assert categories(found, "c") == {"Italy/Turin"}
    assert found["x0.jpg"].reason is not SortReason.TRIP_NEIGHBOUR  # not one trip


def test_a_day_at_home_ends_the_trip(towns: Gazetteer) -> None:
    """Home in between: the two outings are two trips, home is no trip."""
    photos = [*day("a", 1, BRUGES), *day("h", 2, AT_HOME), *day("c", 3, BRUGES)]
    found = run(photos, (TRIP_RULE, PLACE_RULE), towns)
    assert categories(found, "a") == {"Belgium/Bruges"}
    assert found["h0.jpg"].reason is SortReason.PLACE
    assert found["c0.jpg"].reason is SortReason.TRIP


def test_close_to_home_is_no_trip(towns: Gazetteer) -> None:
    """Brussels, 80 km away: under trip_min_km."""
    found = run(day("a", 1, BRUSSELS), (TRIP_RULE,), towns)
    assert found["a0.jpg"].reason is not SortReason.TRIP


def test_photos_without_gps_inside_a_trip_event_inherit_it(towns: Gazetteer) -> None:
    """Three located shots, two without."""
    where = (TURIN, None, TURIN, None, TURIN)
    found = run(outing("t", start_of(1), where), (TRIP_RULE,), towns)
    assert found["t1.jpg"].reason is SortReason.TRIP_NEIGHBOUR
    assert found["t0.jpg"].reason is SortReason.TRIP


def test_a_lone_photo_far_from_home_is_a_trip_of_its_own(towns: Gazetteer) -> None:
    """Not an event, but located and dated."""
    found = run([located("x.jpg", start_of(1), MILAN)], (TRIP_RULE,), towns)
    assert found["x.jpg"].category == "Italy/Milan"


def test_without_the_towns_no_trip_is_found() -> None:
    """The towns are read only when a trip rule is on."""
    found = run(day("t", 1, TURIN), (TRIP_RULE,))
    assert found["t0.jpg"].reason is not SortReason.TRIP


def test_a_trip_category_can_hold_the_region(towns: Gazetteer) -> None:
    """Any of `{country}`, `{region}`, `{city}`, with the date of the event."""
    rule = ClassifyRule(
        name="Holidays", match=RuleMatch.TRIP, category="Holidays/{region} {year}"
    )
    found = run(day("t", 1, TURIN), (rule,), towns)
    assert found["t0.jpg"].category == "Holidays/Piedmont 2023"
