"""The `place` rule: within a personal place's radius, by GPS or by the event."""

from __future__ import annotations

import pytest
from pydantic import ValidationError

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.layout import GeoValues, Values
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.classify.plan_file import RowValues
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.config.classify_places import PersonalPlace
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from tests.support.located import (
    GRANDPA,
    HOME,
    PLACE_RULE,
    TRIP_RULE,
    located,
    outing,
    run,
    start_of,
)

NEAR_HOME = (50.301, 5.101)  # about 130 m away
OUTSIDE = (50.31, 5.1)  # about 1.1 km away
GRANDPA_SPOT = (GRANDPA.latitude, GRANDPA.longitude)


def test_a_photo_within_the_radius_takes_the_place() -> None:
    """Sure, from its own GPS; the folder is the place's name."""
    found = run([located("a.jpg", start_of(1), NEAR_HOME)], (PLACE_RULE,))
    proposal = found["a.jpg"]
    assert (proposal.band, proposal.reason, proposal.rule) == (
        Band.SURE,
        SortReason.PLACE,
        "Places",
    )
    assert proposal.folder == "2023/Home"


def test_a_photo_outside_every_radius_takes_no_place() -> None:
    """One kilometre from home is not home."""
    found = run([located("a.jpg", start_of(1), OUTSIDE)], (PLACE_RULE,))
    assert found["a.jpg"].reason is not SortReason.PLACE


def test_a_receiver_without_a_fix_is_not_a_position() -> None:
    """0, 0 is what a camera writes when it does not know."""
    found = run([located("a.jpg", start_of(1), (0.0, 0.0))], (PLACE_RULE,))
    assert found["a.jpg"].reason is not SortReason.PLACE


def test_photos_without_gps_inherit_the_place_of_their_event() -> None:
    """Three of five shots are located at grandpa's: the two others follow, to check."""
    where = (GRANDPA_SPOT, None, GRANDPA_SPOT, None, GRANDPA_SPOT)
    found = run(outing("g", start_of(2), where), (PLACE_RULE,))
    assert {p.category for p in found.values()} == {"At grandpa's"}
    neighbour = found["g1.jpg"]
    assert (neighbour.reason, neighbour.verdict.score, neighbour.band) == (
        SortReason.PLACE_NEIGHBOUR,
        70,
        Band.UNSURE,
    )


def test_an_event_mostly_elsewhere_gives_no_place_to_its_other_photos() -> None:
    """One shot at home, two far away: the shots without GPS stay unknown."""
    where = (NEAR_HOME, OUTSIDE, OUTSIDE, None, None)
    found = run(outing("e", start_of(3), where), (PLACE_RULE,))
    assert found["e0.jpg"].reason is SortReason.PLACE
    assert found["e3.jpg"].reason is not SortReason.PLACE_NEIGHBOUR


def test_a_rule_category_can_hold_the_place() -> None:
    """`{place}` in a category, and the rule's own score caps its neighbours."""
    rule = ClassifyRule(
        name="Family", match=RuleMatch.PLACE, category="Family/{place}", score=60
    )
    where = (GRANDPA_SPOT, None, GRANDPA_SPOT, GRANDPA_SPOT, GRANDPA_SPOT)
    found = run(outing("f", start_of(4), where), (rule,))
    assert found["f0.jpg"].category == "Family/At grandpa's"
    assert found["f1.jpg"].verdict.score == 60


def test_overlapping_places_the_closest_wins() -> None:
    """Two circles: the photo goes to the one whose centre is closer."""
    garden = PersonalPlace(name="Garden", latitude=50.3015, longitude=5.1, radius_m=500)
    settings = ClassifySettings(rules=(PLACE_RULE,), places=(HOME, garden))
    photo = located("a.jpg", start_of(1), (50.3014, 5.1))  # 156 m from home's centre
    (proposal,) = classify([photo], settings, Scope()).proposals
    assert proposal.category == "Garden"


def test_place_names_are_folder_names_and_unique() -> None:
    """Refused at load time, the name in the message."""
    with pytest.raises(ValidationError, match="Windows"):
        PersonalPlace(name="Home?", latitude=0, longitude=0)
    with pytest.raises(ValidationError, match="braces"):
        PersonalPlace(name="{year}", latitude=0, longitude=0)
    with pytest.raises(ValidationError, match="two places"):
        ClassifySettings(places=(HOME, HOME))
    with pytest.raises(ValidationError, match="only one place can be home"):
        ClassifySettings(places=(HOME, GRANDPA.model_copy(update={"home": True})))
    with pytest.raises(ValidationError, match="latitude"):
        PersonalPlace(name="Pole", latitude=91, longitude=0)


def test_a_trip_rule_needs_a_home() -> None:
    """Without home, there is nothing to be far from."""
    with pytest.raises(ValidationError, match="home = true"):
        ClassifySettings(rules=(TRIP_RULE,), places=(GRANDPA,))


def test_the_plan_file_keeps_the_place_values() -> None:
    """Re-rendered after the user names the event: the place stays."""
    values = Values(2023, 7, 1, "Home", geo=GeoValues(place="Home", country="Italy"))
    row = RowValues.of(values)
    assert (row.place, row.country) == ("Home", "Italy")
    assert row.as_values() == values
    older = RowValues(
        year=2023, month=7, day=1, category="Home", event="", event_start=""
    )
    assert older.as_values().geo == GeoValues()
