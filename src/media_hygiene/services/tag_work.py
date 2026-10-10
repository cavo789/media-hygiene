"""The work of one `tags` run: its files, the photos the model sees, what is missing."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.index.descriptions import PhotoVersion

if TYPE_CHECKING:
    from media_hygiene.classify.models import MediaInput
    from media_hygiene.tags.selection import VisionPlan


@dataclass(frozen=True, slots=True)
class TagWork:
    """The files of a run, the photos the model sees, and those it has not seen yet."""

    files: tuple[MediaInput, ...]
    vision: VisionPlan
    missing: tuple[PhotoVersion, ...]
    seconds_per_photo: float

    @property
    def estimate(self) -> float:
        """How long describing the missing photos should take.

        Returns:
            Seconds.
        """
        return len(self.missing) * self.seconds_per_photo


def version_of(file: MediaInput) -> PhotoVersion:
    """The version of a file the caches are keyed by.

    Args:
        file: The file.

    Returns:
        Its path, size and mtime.
    """
    return PhotoVersion(file.path, file.size, file.mtime_ns)
