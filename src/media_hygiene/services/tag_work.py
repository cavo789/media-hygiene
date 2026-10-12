"""The work of one `tags` run: its files, the photos the model sees, what is missing."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.video_still import still_of

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.scan.video_still import VideoStill
    from media_hygiene.tags.selection import VisionPlan


@dataclass(frozen=True, slots=True)
class TagWork:
    """The files of a run, the photos the model sees, and those it has not seen yet."""

    files: tuple[MediaInput, ...]
    vision: VisionPlan
    missing: tuple[PhotoVersion, ...]
    seconds_per_photo: float
    # The videos the model sees, and the frame each one is seen by.
    stills: Mapping[Path, VideoStill] = field(
        default_factory=lambda: MappingProxyType({})
    )

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


def stills_of(
    files: Iterable[MediaInput], ffmpeg: str | None
) -> dict[Path, VideoStill]:
    """The frame each video among the files is seen by.

    Args:
        files: The photos and videos the model sees.
        ffmpeg: Path of the `ffmpeg` executable; None: no video is seen.

    Returns:
        Video → its frame; empty without `ffmpeg`.
    """
    if ffmpeg is None:
        return {}
    found: dict[Path, VideoStill] = {}
    for file in files:
        if media_kind(file.path) is not MediaKind.VIDEO or file.metadata is None:
            continue
        still = still_of(file.path, file.metadata, ffmpeg)
        if still is not None:
            found[file.path] = still
    return found
