"""The order and the names of an album's copies (0370): by the moment each was taken.

Photos of two cameras mix and a recipient's viewer sorts by name: each copy is named
`NNN_YYYY-MM-DD.jpg`, numbered in the order the photos were taken (the index's
`taken_at`, else the file's date), ties by name. The number is as wide as the count
needs, three digits at least, so a sort by name follows the day.
"""

from __future__ import annotations

import contextlib
import sqlite3
from contextlib import closing
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.plan.bursts import moment_of

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_TAKEN: Final = "SELECT taken_at FROM files WHERE path = ?"
_MIN_DIGITS: Final = 3


@dataclass(frozen=True, slots=True)
class _Dated:
    """A photo and the moment it was taken (the camera's local time read as UTC)."""

    moment: float
    name: str
    photo: Path


def numbered_stems(
    index_file: Path | None, photos: Sequence[Path]
) -> list[tuple[Path, str]]:
    """Each photo, in the order taken, and the name of its copy without extension.

    Args:
        index_file: The index; None or missing: the files' dates alone.
        photos: The photos, in the container.

    Returns:
        `(photo, "007_2023-07-14")` pairs, in order.
    """
    dated = _dated(index_file, photos)
    width = max(_MIN_DIGITS, len(str(len(dated))))
    return [
        (each.photo, f"{number:0{width}d}_{_day(each.moment)}")
        for number, each in enumerate(dated, start=1)
    ]


def _dated(index_file: Path | None, photos: Sequence[Path]) -> list[_Dated]:
    """Each photo with its moment, sorted.

    Args:
        index_file: The index.
        photos: The photos.

    Returns:
        Them, by moment then name.
    """
    taken = _taken(index_file, photos)
    dated = [
        _Dated(_moment(photo, taken.get(photo)), photo.name.casefold(), photo)
        for photo in photos
    ]
    return sorted(dated, key=lambda each: (each.moment, each.name, str(each.photo)))


def _taken(index_file: Path | None, photos: Sequence[Path]) -> dict[Path, str]:
    """The `taken_at` of each photo the index knows, read-only.

    Args:
        index_file: The index.
        photos: The photos.

    Returns:
        Their EXIF dates; empty without an index.
    """
    if index_file is None or not index_file.is_file():
        return {}
    found: dict[Path, str] = {}
    with (
        contextlib.suppress(sqlite3.Error),
        closing(connect_read_only(index_file)) as connection,
    ):
        for photo in photos:
            row = connection.execute(_TAKEN, (str(photo),)).fetchone()
            if row is not None and isinstance(row[0], str):
                found[photo] = row[0]
    return found


def _moment(photo: Path, taken_at: str | None) -> float:
    """When a photo was taken, else its file's date, both as local time read as UTC.

    Args:
        photo: The photo.
        taken_at: Its EXIF date, if any.

    Returns:
        Seconds.
    """
    moment = moment_of(taken_at)
    if moment is not None:
        return moment
    local = datetime.fromtimestamp(photo.stat().st_mtime)  # noqa: DTZ006 - the file's local day
    return local.replace(tzinfo=UTC).timestamp()


def _day(moment: float) -> str:
    """The day of a moment.

    Args:
        moment: Seconds, local time read as UTC.

    Returns:
        `YYYY-MM-DD`.
    """
    return datetime.fromtimestamp(moment, UTC).date().isoformat()
