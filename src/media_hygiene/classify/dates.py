"""The date of each file: EXIF, video tags, file name, folder, then mtime (weak).

Dates are kept naive, in local time: an EXIF date has no zone, and a video's UTC time is
converted with its own offset, or the configured zone. A camera whose clock disagrees
with the folders most of the time is not believed: its folders' dates win.
"""

from __future__ import annotations

from collections import Counter
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from media_hygiene.classify.models import DateSource, Dating

if TYPE_CHECKING:
    import re
    from collections.abc import Sequence
    from datetime import tzinfo

    from media_hygiene.classify.folders import FolderRules
    from media_hygiene.classify.models import MediaInput

_EXIF_FORMATS: Final = ("%Y:%m:%d %H:%M:%S", "%d/%m/%Y %H:%M:%S", "%Y-%m-%d %H:%M:%S")
CONFIDENCE: Final = {
    DateSource.EXIF: 100,
    DateSource.VIDEO: 100,
    DateSource.NAME: 90,
    DateSource.FOLDER: 70,
    DateSource.MTIME: 0,
}
DOUBTED: Final = 60  # an EXIF year its folder contradicts: to check
_MAJORITY: Final = 0.5
_FIRST_YEAR: Final = 1990


def exif_date(text: str | None) -> datetime | None:
    """Read an EXIF date as cameras write it, standard or not.

    Args:
        text: `2019:06:12 14:30:12[.subsec]`, or `12/06/2019 14:30:12`…

    Returns:
        The naive local date, or None.
    """
    if not text:
        return None
    head = text.strip().split(".", 1)[0]
    for pattern in _EXIF_FORMATS:
        try:
            when = datetime.strptime(head, pattern)  # noqa: DTZ007 - EXIF has no zone
        except ValueError:
            continue
        return when if when.year >= _FIRST_YEAR else None
    return None


def video_date(written: str | None, zone: tzinfo) -> datetime | None:
    """Read a video date and bring it to local time.

    Args:
        written: ISO 8601, with `Z` or an offset (`+0100`), as ffprobe printed it.
        zone: The zone for a UTC time without a local offset.

    Returns:
        The naive local date, or None.
    """
    if not written:
        return None
    try:
        when = datetime.fromisoformat(written)
    except ValueError:
        return None
    if when.tzinfo is None:
        return when
    if when.utcoffset():
        return when.replace(tzinfo=None)  # local time with its own offset
    return when.astimezone(zone).replace(tzinfo=None)


def name_date(name: str, patterns: Sequence[re.Pattern[str]]) -> datetime | None:
    """Read a date from a file name.

    Args:
        name: The file name without extension.
        patterns: Patterns with named groups `y`, `m`, `d` (`H`, `M`, `S` optional).

    Returns:
        The date, or None.
    """
    for pattern in patterns:
        found = pattern.fullmatch(name)
        if not found:
            continue
        parts = {key: int(value) for key, value in found.groupdict().items() if value}
        try:
            when = datetime(  # noqa: DTZ001 - local, naive like EXIF
                parts["y"], parts["m"], parts["d"],
                parts.get("H", 12), parts.get("M", 0), parts.get("S", 0),
            )  # fmt: skip
        except KeyError, ValueError:
            continue
        if when.year >= _FIRST_YEAR:
            return when
    return None


def zone_of(name: str) -> tzinfo:
    """The zone for UTC video times.

    Args:
        name: An IANA name, or empty for the container's zone.

    Returns:
        The zone; UTC when unknown.
    """
    if name:
        try:
            return ZoneInfo(name)
        except ZoneInfoNotFoundError, ValueError:
            return UTC
    local = datetime.now().astimezone().tzinfo
    return local or UTC


def clock_not_set(files: Sequence[MediaInput], rules: FolderRules) -> frozenset[str]:
    """Find the cameras whose EXIF year disagrees with the folders most of the time.

    Args:
        files: Every file.
        rules: How folder names give a date.

    Returns:
        Their names (EXIF make and model).
    """
    agree: Counter[str] = Counter()
    disagree: Counter[str] = Counter()
    for file in files:
        taken, folder = exif_date(file.taken_at), rules.year_month(file.path.parent)
        if file.camera and taken and folder:
            counter = agree if taken.year == folder[0] else disagree
            counter[file.camera] += 1
    return frozenset(
        camera
        for camera, count in disagree.items()
        if count / (count + agree[camera]) > _MAJORITY
    )


def folder_dating(file: MediaInput, rules: FolderRules) -> Dating | None:
    """The date its folders give: the 1st of the month, or 1 July of the year.

    Args:
        file: A file.
        rules: How folder names give a date.

    Returns:
        The date, or None.
    """
    found = rules.year_month(file.path.parent)
    if found is None:
        return None
    year, month = found
    when = datetime(year, month or 7, 1)  # noqa: DTZ001 - naive local
    return Dating(when, DateSource.FOLDER, CONFIDENCE[DateSource.FOLDER])
