"""`[[classify.clocks]]`: a camera's clock set right by a rule; future dates doubted."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import UTC, date, datetime, timedelta
from pathlib import Path
from typing import TYPE_CHECKING, Final

import pytest
from pydantic import ValidationError

from media_hygiene.classify.clocks import clocks_of, doubt_future
from media_hygiene.classify.dates import CONFIDENCE, DOUBTED
from media_hygiene.classify.dating import DatingContext, dating_of
from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.models import Band, DateSource, Dating
from media_hygiene.classify.plan_build import build_plan
from media_hygiene.classify.workbook.rows import file_rows
from media_hygiene.classify.workbook.sheets import Labels
from media_hygiene.config.classify_settings import NAME_DATES, ClassifySettings
from media_hygiene.config.clock_settings import parse_shift
from media_hygiene.config.loader import load_settings, write_default_config
from media_hygiene.config.settings import Settings
from media_hygiene.config.tags_settings import TagSettings
from media_hygiene.constants import Locale
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.plan.name_rules import compile_patterns
from media_hygiene.tags.context import tag_context
from media_hygiene.tags.dates import date_words
from media_hygiene.tags.normalize import WordRules
from tests.unit.test_classify_engine import by_name, shot

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations

_CANON: Final = "(?i)canon"
_JULY: Final = {"camera": _CANON, "dates": "2010-07-01..2010-07-15", "shift": "+1h"}
_TODAY: Final = date(2026, 10, 17)
_ON_TRIP: Final = datetime(2010, 7, 10, 9, 0)


def settings(*rules: dict[str, str]) -> ClassifySettings:
    """`[classify]` with these clock rules."""
    return ClassifySettings.model_validate({"clocks": list(rules)})


def chain(*rules: dict[str, str]) -> DatingContext:
    """The date chain with these clock rules, on a fixed day of the run."""
    return DatingContext(
        FolderRules.build((), ((), ())),
        compile_patterns(NAME_DATES),
        UTC,
        clocks=clocks_of(settings(*rules).clocks),
        today=_TODAY,
    )


@pytest.mark.parametrize(
    ("text", "expected"),
    [
        ("+1h", timedelta(hours=1)),
        ("-1d", timedelta(days=-1)),
        ("-1d2h", -timedelta(days=1, hours=2)),
        ("+1d2h30m", timedelta(days=1, hours=2, minutes=30)),
        (" +45m ", timedelta(minutes=45)),
    ],
)
def test_shifts_are_read(text: str, expected: timedelta) -> None:
    """Sign, then days, hours and minutes, combined."""
    assert parse_shift(text) == expected


@pytest.mark.parametrize("text", ["1h", "+", "+1x", "+0h", "+1h1d", "one hour"])
def test_bad_shifts_are_refused(text: str) -> None:
    """No sign, no amount, an unknown unit, nothing shifted, units out of order."""
    with pytest.raises(ValueError, match="shift"):
        parse_shift(text)


@pytest.mark.parametrize(
    ("field", "value"),
    [
        ("shift", "+1x"),
        ("dates", "2010-07-15..2010-07-01"),
        ("dates", "July"),
        ("camera", "(canon"),
    ],
)
def test_a_bad_rule_is_refused_naming_its_camera(field: str, value: str) -> None:
    """A bad shift, range or pattern stops the settings, naming the rule."""
    with pytest.raises(ValidationError, match="clock '"):
        settings({**_JULY, field: value})


def test_two_rules_of_one_camera_may_not_overlap() -> None:
    """Both ranges are named; another camera on the same days is fine."""
    later = {**_JULY, "dates": "2010-07-15..2010-07-20", "shift": "-1d"}
    with pytest.raises(
        ValidationError, match=r"2010-07-01\.\.2010-07-15 and 2010-07-15"
    ):
        settings(_JULY, later)
    nikon = {**later, "camera": "(?i)nikon"}
    assert len(settings(_JULY, nikon).clocks) == 2


def test_the_shift_applies_to_the_camera_inside_its_range() -> None:
    """Canon in July 2010: +1h, noted; the phone and other days untouched."""
    context = chain(_JULY)
    canon = dating_of(shot("a.jpg", _ON_TRIP, "Canon EOS 550D"), context)
    assert canon == Dating(
        _ON_TRIP + timedelta(hours=1), DateSource.EXIF, 100, clock=("+1h", _CANON)
    )
    phone = dating_of(shot("b.jpg", _ON_TRIP, "Pixel 7"), context)
    assert phone.when == _ON_TRIP
    assert phone.clock is None
    august = datetime(2010, 8, 1, 9)
    assert dating_of(shot("c.jpg", august, "Canon EOS"), context).when == august


def test_a_camera_a_day_behind_joins_the_phone_s_event() -> None:
    """Without the rule, two events a day apart; with it, one, in the right order."""
    phone = [shot(f"p{i}.jpg", _ON_TRIP + timedelta(minutes=i * 20)) for i in range(5)]
    late = _ON_TRIP - timedelta(days=1) + timedelta(minutes=10)
    canon = [
        shot(f"c{i}.jpg", late + timedelta(minutes=i * 20), "Canon EOS")
        for i in range(5)
    ]
    rule = {**_JULY, "dates": "2010-07-09", "shift": "+1d"}
    files = [*phone, *canon]
    assert len(classify(files, settings(), Scope()).events) == 2
    shifted = classify(files, settings(rule), Scope())
    assert len(shifted.events) == 1
    (event,) = shifted.events
    assert [path.name for path in event.paths][:4] == [
        "p0.jpg",
        "c0.jpg",
        "p1.jpg",
        "c1.jpg",
    ]


def test_a_future_date_is_doubted() -> None:
    """After the day of the run: confidence capped, flagged; today is believed."""
    future = Dating(datetime(2030, 1, 1), DateSource.EXIF, 100)
    assert doubt_future(future, _TODAY) == Dating(
        future.when, DateSource.EXIF, DOUBTED, future=True
    )
    today = Dating(datetime(2026, 10, 17, 23), DateSource.EXIF, 100)
    assert doubt_future(today, _TODAY) == today
    found = dating_of(shot("a.jpg", datetime(2031, 5, 1)), chain())
    assert found.future
    assert found.confidence == DOUBTED


def test_a_future_date_goes_to_check_and_the_workbook_says_why() -> None:
    """In a named folder, a date ahead goes to "to check"; the row says why."""
    rule = {**_JULY, "dates": "2099-01-01..2099-12-31"}
    files = [
        shot("Seaside/a.jpg", datetime(2099, 6, 1), "Canon"),
        shot("Seaside/b.jpg", _ON_TRIP, "Canon"),
    ]
    found = classify(files, settings(rule), Scope())
    bands = {name: p.band for name, p in by_name(found.proposals).items()}
    assert bands == {"a.jpg": Band.UNSURE, "b.jpg": Band.SURE}
    plan = build_plan(found, settings(rule), HostPathMapper(Path("/data")))
    rows = {row[3]: row[5] for row in file_rows(plan, Labels.current())}
    assert rows["a.jpg"] == (
        "camera (EXIF), +1h: rule (?i)canon, in the future: to check"
    )
    assert rows["b.jpg"] == "camera (EXIF)"
    assert plan.rows[0].clock == ("+1h", _CANON)


def test_tags_words_follow_the_clock() -> None:
    """A camera a day behind on 31 December: its photo of New Year's Day is 2011."""
    rule = {"camera": _CANON, "dates": "2010-12-31", "shift": "+1d"}
    chosen = Settings.model_validate({"classify": {"clocks": [rule]}})
    tags = TagSettings.model_validate({"language": "en"})
    words = tag_context(chosen, WordRules.of(tags, Locale.EN))
    file = shot("a.jpg", datetime(2010, 12, 31, 10), "Canon EOS")
    assert date_words(file, words)[:2] == ("2011", "January")
    plain = tag_context(Settings(), WordRules.of(tags, Locale.EN))
    assert date_words(file, plain)[:2] == ("2010", "December")


def test_the_confidence_of_a_plain_date_is_kept() -> None:
    """No rule, no future: the chain is unchanged."""
    found = dating_of(shot("a.jpg", _ON_TRIP, "Canon"), chain())
    assert found == Dating(_ON_TRIP, DateSource.EXIF, CONFIDENCE[DateSource.EXIF])


def test_the_template_holds_an_example_that_loads(locations: Locations) -> None:
    """`config.toml` shows a commented clock; uncommented, it is read as written."""
    assert write_default_config(locations.config_file, Locale.EN)
    text = locations.config_file.read_text("utf-8")
    assert "# [[classify.clocks]]" in text
    lines = text.splitlines()
    start = lines.index("# [[classify.clocks]]")
    example = "\n".join(line.removeprefix("# ") for line in lines[start : start + 4])
    locations.config_file.write_text(example + "\n", "utf-8")
    clocks = load_settings(locations).settings.classify.clocks
    assert [(c.dates, c.shift) for c in clocks] == [("2010-07-01..2010-07-15", "+1h")]
