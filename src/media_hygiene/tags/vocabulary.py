"""The words of dates, in the languages of the tags: months, seasons, holidays.

Data, not interface text: the tags follow `[tags] language`, not the interface, so
they are written here in each language instead of going through gettext.
"""

from __future__ import annotations

from datetime import date, timedelta
from typing import Final

from media_hygiene.classify.rules.calendar import Recurring
from media_hygiene.constants import Locale

MONTH_NAMES: Final = {
    Locale.FR: (
        *("janvier", "février", "mars", "avril", "mai", "juin", "juillet"),
        *("août", "septembre", "octobre", "novembre", "décembre"),
    ),
    Locale.EN: (
        *("January", "February", "March", "April", "May", "June", "July"),
        *("August", "September", "October", "November", "December"),
    ),
}
# Winter, spring, summer, autumn: the meteorological seasons, by month.
SEASON_NAMES: Final = {
    Locale.FR: ("hiver", "printemps", "été", "automne"),
    Locale.EN: ("winter", "spring", "summer", "autumn"),
}
SEASON_OF_MONTH: Final = (0, 0, 1, 1, 1, 2, 2, 2, 3, 3, 3, 0)  # January first
HALF_YEAR: Final = 2  # seasons: the southern hemisphere is two seasons apart
# The days of every year that a photo of the family is often about.
FIXED_HOLIDAYS: Final = (
    (Recurring((12, 24), (12, 26)), {Locale.FR: "Noël", Locale.EN: "Christmas"}),
    (
        Recurring((12, 31), (1, 1)),
        {Locale.FR: "Nouvel an", Locale.EN: "New Year"},
    ),
    (
        Recurring((12, 6), (12, 6)),
        {Locale.FR: "Saint-Nicolas", Locale.EN: "Saint Nicholas"},
    ),
    (
        Recurring((2, 14), (2, 14)),
        {Locale.FR: "Saint-Valentin", Locale.EN: "Valentine's Day"},
    ),
    (Recurring((10, 31), (10, 31)), {Locale.FR: "Halloween", Locale.EN: "Halloween"}),
)
EASTER: Final = {Locale.FR: "Pâques", Locale.EN: "Easter"}
_EASTER_DAYS: Final = 2  # Sunday and Monday


def easter_sunday(year: int) -> date:
    """Easter Sunday of a year (Gregorian calendar, anonymous algorithm).

    Args:
        year: The year.

    Returns:
        The day.
    """
    golden = year % 19
    century, of_century = divmod(year, 100)
    leap_century, century_rest = divmod(century, 4)
    lag = (century + 8) // 25
    moon_lag = (century - lag + 1) // 3
    epact = (19 * golden + century - leap_century - moon_lag + 15) % 30
    leap, rest = divmod(of_century, 4)
    weekday = (32 + 2 * century_rest + 2 * leap - epact - rest) % 7
    shift = (golden + 11 * epact + 22 * weekday) // 451
    month, day = divmod(epact + weekday - 7 * shift + 114, 31)
    return date(year, month, day + 1)


def is_easter(day: date) -> bool:
    """Tell whether a day is Easter Sunday or Easter Monday.

    Args:
        day: A day.

    Returns:
        True on those two days.
    """
    gap = day - easter_sunday(day.year)
    return timedelta(0) <= gap < timedelta(days=_EASTER_DAYS)
