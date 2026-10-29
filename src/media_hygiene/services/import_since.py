"""`import --since`: only the files of a period: today, this week, this month (0476).

A file's day is the date in its name when there is one (`20261029_143000.jpg`,
`IMG_20261029_…`, `VID_…`, `PXL_…`, `Screenshot_2026-10-29-…`), else its modified time:
no EXIF is read over USB (a file a request, too slow: estimated from the 31 ms a file of
the listing alone). Without `--since`, a phone import takes what came since the last
one: `mh` writes the day of each import that copied files into the journal folder
(`last-import.txt`); the first import takes all.
"""

from __future__ import annotations

import re
from datetime import UTC, date, datetime, timedelta
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

# The file `mh` writes in the journal folder after a phone import: its day, ISO.
LAST_IMPORT_FILE: Final = "last-import.txt"
# `--since week`: today and the six days before it.
WEEK_DAYS: Final = 7
# A day in a name: 2026-10-29 or 20261029, not inside a longer number.
_NAME_DAY: Final = re.compile(
    r"(?<!\d)((?:19|20)\d{2})-?(0[1-9]|1[0-2])-?(0[1-9]|[12]\d|3[01])(?!\d)"
)
_BOM: Final = "﻿"


class Span(StrEnum):
    """The periods `--since` takes by name; a day `YYYY-MM-DD` is taken too."""

    TODAY = "today"
    WEEK = "week"
    MONTH = "month"
    ALL = "all"


def name_day(name: str) -> date | None:
    """The day a phone or a camera wrote in a file's name.

    Args:
        name: The file name.

    Returns:
        That day, or None when the name holds no valid one.
    """
    for found in _NAME_DAY.finditer(name):
        try:
            return date(int(found[1]), int(found[2]), int(found[3]))
        except ValueError:
            continue
    return None


def file_day(name: str, modified: str) -> date | None:
    """A file's day: the one in its name, else its modified time (ISO, UTC or local).

    Args:
        name: The file name.
        modified: Its modified time as listed (`2026-10-29T10:00:00Z`), may be empty.

    Returns:
        Its day, or None when neither tells one.
    """
    if (day := name_day(name)) is not None:
        return day
    try:
        moment = datetime.fromisoformat(modified)
    except ValueError:
        return None
    if moment.tzinfo is None:
        return moment.date()
    return moment.astimezone().date()


def first_day(since: str | None, today: date, last: date | None) -> date | None:
    """The first day a file must have to be imported.

    Args:
        since: `--since` as typed; None: since the last import.
        today: Today, local.
        last: The day of the last import, if any.

    Returns:
        The first day kept, or None: every file.

    Raises:
        ConfigError: `--since` is neither a period nor a day.
    """
    if since is None:
        return last
    word = since.strip().casefold()
    starts = {
        Span.TODAY.value: today,
        Span.WEEK.value: today - timedelta(days=WEEK_DAYS - 1),
        Span.MONTH.value: today.replace(day=1),
    }
    if word in starts:
        return starts[word]
    if word == Span.ALL.value:
        return None
    try:
        return date.fromisoformat(word)
    except ValueError:
        raise ConfigError(
            _("--since takes today, week, month, all or a day such as 2026-10-29."),
            _("For example: mh import --phone --since week"),
        ) from None


def kept(name: str, modified: str, first: date | None) -> bool:
    """Whether a file is in the period: an unknown day is kept (never lost).

    Args:
        name: The file name.
        modified: Its modified time as listed.
        first: The first day kept; None: every file.

    Returns:
        True when it is imported.
    """
    if first is None:
        return True
    day = file_day(name, modified)
    return day is None or day >= first


def last_import(journal_dir: Path) -> date | None:
    """The day of the last phone import, as `mh` wrote it.

    Args:
        journal_dir: The journal folder.

    Returns:
        That day, or None: none yet, or a file that cannot be read.
    """
    try:
        text = (journal_dir / LAST_IMPORT_FILE).read_text(encoding="utf-8")
        return date.fromisoformat(text.strip().lstrip(_BOM)[:10])
    except OSError, ValueError:
        return None


def today_local() -> date:
    """Today, on this machine's clock.

    Returns:
        The day.
    """
    return datetime.now(UTC).astimezone().date()
