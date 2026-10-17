"""The date of a file in `classify`: where it comes from, how much it is trusted."""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from datetime import datetime


class DateSource(StrEnum):
    """Where the date of a file comes from, the most reliable first."""

    EXIF = "exif"
    VIDEO = "video"
    TAKEOUT = "takeout"  # the `.json` of a Google Photos Takeout
    NAME = "name"
    FOLDER = "folder"
    MTIME = "mtime"


@dataclass(frozen=True, slots=True)
class Dating:
    """The date of a file, where it comes from, and how much it is trusted (0-100)."""

    when: datetime
    source: DateSource
    confidence: int
    # The `[[classify.clocks]]` rule that set the camera's clock right: (shift, camera).
    clock: tuple[str, str] | None = None
    future: bool = False  # after the day of the run: doubted, to check
