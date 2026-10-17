"""Copies messaging apps and e-mail clients keep: where they lie, the day they name.

WhatsApp strips the EXIF of the pictures it sends, but their names still carry the
day (`IMG-20190712-WA0003.jpg`, `VID-20190712-WA0001.mp4`): `classify` reads the
same patterns.
"""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.dates import exif_date, name_date, video_date, zone_of
from media_hygiene.config.classify_defaults import NAME_DATES
from media_hygiene.plan.name_rules import compile_patterns

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path

# Folders where messaging apps and e-mail clients save what they receive or send.
MESSAGING_FOLDERS: Final = tuple(
    re.compile(pattern, re.IGNORECASE)
    for pattern in (
        r"whatsapp( .*)?",
        r"telegram( .*)?",
        r"signal( .*)?",
        r"messenger",
        r"viber( .*)?",
        r"wechat( .*)?",
        r"e-?mails?",
        r"outlook",
        r"thunderbird",
        r".*attachments?",
        r"pi[eè]ces[ -]jointes",
    )
)
# The dates `classify` reads in file names (`IMG-20190712-WA0003`): the day of a copy
# whose messaging app stripped the EXIF.
_NAME_DATES: Final = compile_patterns(NAME_DATES)


def same_day(taken_at: str | None, copy: Path) -> bool:
    """Tell whether the name of a copy is dated the day the kept version was taken.

    Args:
        taken_at: The date of the kept version: EXIF, or a video's ISO 8601 time.
        copy: The copy, without a date of its own.

    Returns:
        True when both days are known and the same (a name has no time).
    """
    kept = _day(taken_at)
    named = name_date(copy.stem, _NAME_DATES)
    return kept is not None and named is not None and named.date() == kept


def _day(taken_at: str | None) -> date | None:
    """The local day of a date as the scan read it.

    Args:
        taken_at: An EXIF date, or a video's ISO 8601 time (UTC brought to local time).

    Returns:
        The day, or None when there is no readable date.
    """
    if not taken_at:
        return None
    when = exif_date(taken_at) or video_date(taken_at, zone_of(""))
    return None if when is None else when.date()


def in_messaging_folder(path: Path) -> bool:
    """Tell whether a file lies in a folder of a messaging app or an e-mail client.

    Args:
        path: The file.

    Returns:
        True when one of its folders is named like one.
    """
    return any(
        pattern.fullmatch(folder)
        for folder in path.parent.parts
        for pattern in MESSAGING_FOLDERS
    )
