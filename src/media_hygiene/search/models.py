"""What a search finds: the files, best first, with their tags."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.tags.models import TagSource


@dataclass(frozen=True, slots=True)
class Hit:
    """One file found: its key in the index, the file, its date and its tags."""

    key: int  # the row of the file in the index: names its previews
    photo: PhotoVersion
    date: str | None  # `YYYY-MM-DD`, when the file says when it was taken
    tags: Mapping[TagSource, tuple[str, ...]]
    facts: str = ""  # a video: `12 min · 12.7 Mb/s · mjpeg` and its size (0408)


@dataclass(frozen=True, slots=True)
class Found:
    """How many files match, and the first ones, best first."""

    total: int
    hits: tuple[Hit, ...]
