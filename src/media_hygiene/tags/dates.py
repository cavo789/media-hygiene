"""The words of a date: year, month, season, holidays and the user's own days.

The date is the one `classify` reads (EXIF, else the video's own date, else the one a
Google Photos Takeout `.json` records); without one, the year and month a folder name
gives (`2007/Avril`). A position in the southern hemisphere turns the seasons around.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.clocks import set_right
from media_hygiene.classify.dates import takeout_date, video_date
from media_hygiene.classify.whereabouts import located_point
from media_hygiene.tags.vocabulary import (
    EASTER,
    FIXED_HOLIDAYS,
    HALF_YEAR,
    MONTH_NAMES,
    SEASON_NAMES,
    SEASON_OF_MONTH,
    is_easter,
)

if TYPE_CHECKING:
    from datetime import date

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.tags.context import TagContext


def date_words(file: MediaInput, context: TagContext) -> tuple[str, ...]:
    """The words of the date a file was taken.

    Args:
        file: The file and what the index knows of it.
        context: The language, the zone of the videos, the user's date rules.

    Returns:
        E.g. `2007`, `avril`, `printemps`, `Pâques`; empty without any date.
    """
    language = context.words.language
    day = taken_on(file, context)
    if day is None:
        found = context.folders.year_month(file.path.parent)
        if found is None:
            return ()
        year, month = found
        if month is None:
            return (str(year),)
        return (str(year), *_month(file, month, context))
    holidays = [
        names[language] for window, names in FIXED_HOLIDAYS if window.contains(day)
    ]
    if is_easter(day):
        holidays.append(EASTER[language])
    own = [name for window, name in context.calendar if window.contains(day)]
    return (str(day.year), *_month(file, day.month, context), *holidays, *own)


def taken_on(file: MediaInput, context: TagContext) -> date | None:
    """The day a file was taken, read as `classify` reads it.

    Args:
        file: The file.
        context: The zone of the videos' UTC times, the clocks set right.

    Returns:
        The local day, or None.
    """
    when = set_right(file, context.clocks)
    if when is None and file.metadata is not None:
        when = video_date(file.metadata.recorded_at, context.zone)
    if when is None and file.takeout is not None:
        when = takeout_date(file.takeout.taken_at, context.zone)
    return when.date() if when is not None else None


def _month(file: MediaInput, month: int, context: TagContext) -> tuple[str, str]:
    """The name of a month and its season.

    Args:
        file: The file: below the equator, the seasons are the other way round.
        month: 1 to 12.
        context: The language.

    Returns:
        The month and the season.
    """
    language = context.words.language
    season = SEASON_OF_MONTH[month - 1]
    point = located_point(file.metadata)
    if point is not None and point.latitude < 0:
        season = (season + HALF_YEAR) % len(SEASON_NAMES[language])
    return MONTH_NAMES[language][month - 1], SEASON_NAMES[language][season]
