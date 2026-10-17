"""The day of a file's date, whatever form it was written in: a SQLite function.

The index keeps a date as the file writes it (a fact): `2004:12:04 11:05:08` (EXIF),
`2004-12-04T10:00:00Z` (a video), or `04/12/2004 11:05:08` (some cameras write the day
first). The search reads them all as `2004-12-04`; a date naming no real day
(`0000:00:00 00:00:00`) is no date: out of every year filter, listed last.
"""

from __future__ import annotations

from datetime import date
from functools import lru_cache
from typing import Final

from media_hygiene.classify.dates import exif_datetime

NAME: Final = "media_day"
_DAY_LENGTH: Final = 10  # `YYYY:MM:DD`, then the time
_SEPARATORS: Final = frozenset(":-")
_YEAR_END, _MONTH_END = 4, 7
_DAYS_KEPT: Final = 65_536  # distinct days remembered: a lifetime of photos is ~20,000


def media_day(text: str | None) -> str | None:
    """The day a written date names, as `YYYY-MM-DD`.

    The year-first forms (EXIF and ISO, nearly every file) are read from their first
    ten characters, without `strptime`, and each distinct day once: this runs for every
    row of a search.

    Args:
        text: The date as the file writes it, or None.

    Returns:
        `YYYY-MM-DD`, or None when the text names no real day.
    """
    if not text:
        return None
    head = text[:_DAY_LENGTH]
    separator = head[_YEAR_END : _YEAR_END + 1]
    if separator in _SEPARATORS and head[_MONTH_END : _MONTH_END + 1] == separator:
        return _year_first_day(head)
    when = exif_datetime(text)
    return when.date().isoformat() if when is not None else None


@lru_cache(maxsize=_DAYS_KEPT)
def _year_first_day(head: str) -> str | None:
    """Read `YYYY:MM:DD` or `YYYY-MM-DD`.

    Args:
        head: The first ten characters of a date.

    Returns:
        `YYYY-MM-DD`, or None when it names no real day (`0000:00:00`).
    """
    try:
        day = date(int(head[:_YEAR_END]), int(head[5:_MONTH_END]), int(head[8:]))
    except ValueError:
        return None
    return day.isoformat()
