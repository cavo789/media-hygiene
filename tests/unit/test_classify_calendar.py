"""Dates written in rules: recurring days, one-off ranges, days that do not exist."""

from __future__ import annotations

from datetime import date

import pytest

from media_hygiene.classify.rules.calendar import parse_one_off, parse_recurring


def test_a_recurring_window_comes_back_every_year() -> None:
    """Christmas, 24 to 26 December, whatever the year."""
    christmas = parse_recurring("12-24..12-26")
    assert christmas.contains(date(2016, 12, 25))
    assert christmas.contains(date(2023, 12, 26))
    assert not christmas.contains(date(2016, 12, 27))


def test_a_recurring_window_crosses_new_year() -> None:
    """`12-31..01-01`: both nights, not the rest of the year."""
    new_year = parse_recurring("12-31..01-01")
    assert new_year.contains(date(2016, 12, 31))
    assert new_year.contains(date(2017, 1, 1))
    assert not new_year.contains(date(2017, 1, 2))
    assert not new_year.contains(date(2016, 12, 30))


def test_a_single_day_and_a_leap_day() -> None:
    """`03-12` is one day; `02-29` exists in leap years."""
    birthday = parse_recurring(" 03-12 ")
    assert birthday.contains(date(2018, 3, 12))
    assert not birthday.contains(date(2018, 3, 13))
    assert parse_recurring("02-29").contains(date(2020, 2, 29))


def test_a_one_off_range_happens_once() -> None:
    """A trip: inside the range only, that year only."""
    italy = parse_one_off("2023-07-01..2023-07-15")
    assert italy.contains(date(2023, 7, 15))
    assert not italy.contains(date(2024, 7, 5))
    assert italy.overlaps(parse_one_off("2023-07-15..2023-07-20"))
    assert not italy.overlaps(parse_one_off("2023-07-16"))


@pytest.mark.parametrize("text", ["02-30", "13-01", "24/12", "12-24..", "Christmas"])
def test_a_recurring_day_that_does_not_exist_is_refused(text: str) -> None:
    """A day that no year has, or a format that is not `MM-DD`."""
    with pytest.raises(ValueError, match="day"):
        parse_recurring(text)


@pytest.mark.parametrize(
    ("text", "said"),
    [
        ("2023-02-30", "not a date range"),
        ("2023-07-15..2023-07-01", "ends before it starts"),
        ("July 2023", "not a date range"),
    ],
)
def test_a_wrong_date_range_is_refused(text: str, said: str) -> None:
    """A day that does not exist, a range backwards, a free text."""
    with pytest.raises(ValueError, match=said):
        parse_one_off(text)
