"""What a search finds: the files, best first, with their tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.tags.models import TagSource


@dataclass(frozen=True, slots=True)
class Hit:  # pylint: disable=too-many-instance-attributes
    """One file found: its key in the index, the file, its date and its tags."""

    key: int  # the row of the file in the index: names its previews
    photo: PhotoVersion
    date: str | None  # `YYYY-MM-DD`, when the file says when it was taken
    tags: Mapping[TagSource, tuple[str, ...]]
    facts: str = ""  # a video: `12 min · 12.7 Mb/s · mjpeg` and its size (0408)
    taken: str = ""  # `2023-07-14 10:32`: when it was taken, from its metadata (0433)
    exif: tuple[str, ...] = ()  # what its metadata says, one fact per line (0433)
    seconds: float | None = None  # a video's length, for its badge (0434)


@dataclass(frozen=True, slots=True)
class Found:
    """How many files match, and the first ones, best first."""

    total: int
    hits: tuple[Hit, ...]
