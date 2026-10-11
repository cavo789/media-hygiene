"""The small previews of the search grid, kept in the cache folder between searches.

A preview is named after the file and its version: a file changed since gets a new
one. Rendered in the worker pool; a cache folder that cannot be written only means
the preview is rendered again next time.
"""

from __future__ import annotations

import contextlib
import hashlib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.report.thumbnails import jpeg_preview

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.descriptions import PhotoVersion

PREVIEWS_DIR_NAME: Final = "search-previews"
# Sharp on a high-density screen at the grid's size.
_GRID_EDGE: Final = 360
_NAME_LENGTH: Final = 24
_SUFFIX: Final = ".jpg"


@dataclass(frozen=True, slots=True)
class GridPreview:
    """One preview of the grid: the file, and the folder previews are kept in."""

    photo: PhotoVersion
    folder: Path


def grid_preview(job: GridPreview) -> bytes | None:
    """Read the preview from the cache, or render it and keep it there.

    Runs in a worker process.

    Args:
        job: The file and the cache folder.

    Returns:
        The JPEG bytes, or None when the file cannot be shown (a video, a broken
        picture).
    """
    target = job.folder / _name(job.photo)
    with contextlib.suppress(OSError):
        return target.read_bytes()
    image = jpeg_preview(job.photo.path, _GRID_EDGE)
    if image is None:
        return None
    with contextlib.suppress(OSError):
        job.folder.mkdir(parents=True, exist_ok=True)
        partial = target.with_suffix(".part")
        partial.write_bytes(image)
        partial.replace(target)
    return image


def _name(photo: PhotoVersion) -> str:
    """Name the preview of one version of a file.

    Args:
        photo: The file, its size and mtime.

    Returns:
        A file name such as `0f3a….jpg`.
    """
    key = f"{photo.path}\0{photo.size}\0{photo.mtime_ns}"
    return hashlib.sha256(key.encode()).hexdigest()[:_NAME_LENGTH] + _SUFFIX
