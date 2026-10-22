"""The picture the TV shows: the photo upright, fitted to the screen, kept in the cache.

A 2012 TV decodes a 5 MB photo in about 2 s, the same photo at 1920 px in about 1 s
(measured by eye on the maintainer's UE55ES6100, 2026-10-21): the TV gets a JPEG fitted
into `screen_px` x `screen_px * 9 / 16` (1920 x 1080 by default), its EXIF orientation
applied, quality `SCREEN_QUALITY`, baseline (never progressive: drawn once, whole). Kept
in the cache folder next to the other previews, named after the file's version and the
size: each photo is made once per screen size, and trimmed with them
(`[cache] previews_max_gb`). Runs in the worker pool.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.report.preview_cache import keep_preview
from media_hygiene.report.thumbnails import JpegFit, fitted_jpeg

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

SCREEN_QUALITY: Final = 85
WIDE: Final = (16, 9)  # the shape of a TV
SQUARE: Final = (1, 1)  # a phone, held upright or turned: a photo fits either way
_VERSION: Final = 1  # raise it when the TV's pictures are made differently
_NAME_LENGTH: Final = 32
_LABEL: Final = "screen"


@dataclass(frozen=True, slots=True)
class ScreenJob:
    """The size of a screen's pictures, and the folder keeping them (None: none)."""

    screen_px: int
    folder: Path | None
    shape: tuple[int, int] = WIDE  # a TV; `SQUARE` for a phone turned either way (0297)

    @property
    def box(self) -> tuple[int, int]:
        """The largest picture the screen gets.

        Returns:
            Width and height: `screen_px` wide, in the screen's shape.
        """
        width, height = self.shape
        return self.screen_px, self.screen_px * height // width

    def renderer(self) -> Callable[[Path], bytes | None]:
        """A function making one photo's picture, for the worker pool.

        Returns:
            It, picklable.
        """
        return partial(kept_screen_jpeg, self)


def kept_screen_jpeg(job: ScreenJob, source: Path) -> bytes | None:
    """Read the TV's picture from the cache, or make it and keep it there.

    Args:
        job: The size and the cache folder.
        source: The photo, in the container.

    Returns:
        The JPEG; None when the photo cannot be decoded (kept as an empty file).
    """
    if job.folder is None:
        return screen_jpeg(source, job.box)
    try:
        version = source.stat()
    except OSError:
        return None
    key = f"{_LABEL}\0{_VERSION}\0{source}\0{version.st_size}\0{version.st_mtime_ns}"
    size = f"{job.screen_px}" if job.shape == WIDE else f"{job.screen_px}\0{job.shape}"
    name = hashlib.sha256(f"{key}\0{size}".encode()).hexdigest()
    target = job.folder / f"{name[:_NAME_LENGTH]}.jpg"
    with contextlib.suppress(OSError):
        kept = target.read_bytes()
        os.utime(target)  # used now: trimmed last
        return kept or None  # empty: this version cannot be shown
    picture = screen_jpeg(source, job.box)
    keep_preview(target, picture or b"")
    return picture


def screen_jpeg(source: Path, box: tuple[int, int]) -> bytes | None:
    """Make the TV's picture of a photo: upright, fitted into the box.

    Args:
        source: Image or RAW file.
        box: The largest width and height.

    Returns:
        The JPEG, or None when the photo cannot be decoded.
    """
    return fitted_jpeg(source, JpegFit(box, SCREEN_QUALITY))
