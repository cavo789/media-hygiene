"""Dates written in rules: days that come back every year, and one-off date ranges.

`12-24..12-26` comes back every year, and `12-31..01-01` crosses New Year;
`2023-07-01..2023-07-15` happens once. A date that does not exist is refused.
"""

from __future__ import annotations

import re
from dataclasses import dataclass
from datetime import date
from typing import Final

_SEPARATOR: Final = ".."
_DAY: Final = re.compile(r"(?P<month>\d{1,2})-(?P<day>\d{1,2})")
_LEAP_YEAR: Final = 2000  # a recurring 02-29 exists


@dataclass(frozen=True, slots=True)
class Recurring:
    """Days of the year, from `start` to `end` (month, day), both included."""

    start: tuple[int, int]
    end: tuple[int, int]

    def contains(self, day: date) -> bool:
        """Tell whether a day falls in the window, whatever its year.

        Args:
            day: A day.

        Returns:
            True when it does; a window whose end comes before its start crosses
            New Year.
        """
        key = (day.month, day.day)
        if self.start <= self.end:
            return self.start <= key <= self.end
        return key >= self.start or key <= self.end


@dataclass(frozen=True, slots=True)
class OneOff:
    """A date range that happens once, both days included."""

    start: date
    end: date

    def contains(self, day: date) -> bool:
        """Tell whether a day falls in the range.

        Args:
            day: A day.

        Returns:
            True when it does.
        """
        return self.start <= day <= self.end

    def overlaps(self, other: OneOff) -> bool:
        """Tell whether two ranges share a day.

        Args:
            other: Another range.

        Returns:
            True when they do.
        """
        return self.start <= other.end and other.start <= self.end


def parse_recurring(text: str) -> Recurring:
    """Read `MM-DD` or `MM-DD..MM-DD`.

    Args:
        text: The `dates` of a `calendar` rule.

    Returns:
        The window.

    Raises:
        ValueError: The text is not written so, or names a day that does not exist.
    """
    first, last = _halves(text)
    return Recurring(_month_day(first), _month_day(last))


def parse_one_off(text: str) -> OneOff:
    """Read `YYYY-MM-DD` or `YYYY-MM-DD..YYYY-MM-DD`.

    Args:
        text: The `dates` of a `date_range` rule.

    Returns:
        The range.

    Raises:
        ValueError: The text is not written so, names a day that does not exist, or
            ends before it starts.
    """
    first, last = _halves(text)
    try:
        start, end = date.fromisoformat(first), date.fromisoformat(last)
    except ValueError as exc:
        message = f"{text!r} is not a date range such as 2023-07-01..2023-07-15"
        raise ValueError(message) from exc
    if end < start:
        message = f"{text!r} ends before it starts"
        raise ValueError(message)
    return OneOff(start, end)


def _halves(text: str) -> tuple[str, str]:
    """Split `start..end`; a single day is its own start and end.

    Args:
        text: The dates.

    Returns:
        Start and end, stripped.
    """
    first, separator, last = text.partition(_SEPARATOR)
    return first.strip(), (last if separator else first).strip()


def _month_day(text: str) -> tuple[int, int]:
    """Read one `MM-DD`.

    Args:
        text: E.g. `12-24`.

    Returns:
        Month and day.

    Raises:
        ValueError: Not written so, or no such day in a leap year.
    """
    found = _DAY.fullmatch(text)
    if found is None:
        message = f"{text!r} is not a day of the year such as 12-24"
        raise ValueError(message)
    month, day = int(found["month"]), int(found["day"])
    try:
        date(_LEAP_YEAR, month, day)
    except ValueError as exc:
        message = f"{text!r} is not a day that exists"
        raise ValueError(message) from exc
    return month, day
