"""Previews kept in the cache folder: each photo is decoded once per size.

A preview is named after the file's path, size and modification time, its size in
pixels and the way previews are made (`_VERSION`): a file changed since gets a new
one. Written under a temporary name, then renamed, so a crash never leaves half a
JPEG. A picture that cannot be decoded is kept as an empty file: that version of it
is not decoded again either. A cache folder that cannot be written only means the
preview is rendered again next time. Without a persistent `/cache`, nothing is kept.
"""

from __future__ import annotations

import contextlib
import hashlib
import os
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.report.thumbnails import jpeg_preview
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Callable
    from concurrent.futures import Executor
    from pathlib import Path

# Raise it when previews are made differently: every preview is then made again.
_VERSION: Final = 1
# Videos got a frame in 0373: their empty previews of before (no picture) are not read.
_VIDEO_VERSION: Final = 2
_NAME_LENGTH: Final = 32
_SUFFIX: Final = ".jpg"
_PARTIAL: Final = ".part"
# Beyond the bound (`[cache] previews_max_gb`), the previews used least recently go,
# down to this share of it (so that the next report does not trim again).
_TRIMMED_SHARE: Final = 0.8


@dataclass(frozen=True, slots=True)
class PreviewJob:
    """One preview: the picture, its longer side, the folder previews are kept in."""

    source: Path
    edge: int
    folder: Path | None


@dataclass(frozen=True, slots=True)
class PreviewPool:
    """Where previews are rendered (the worker pool) and kept (None: nowhere)."""

    executor: Executor
    folder: Path | None = None

    def renderer(self, edge: int) -> Callable[[Path], bytes | None]:
        """A function rendering one picture at this size, for the pool.

        Args:
            edge: The longer side, in pixels.

        Returns:
            It, picklable: it runs in a worker process.
        """
        return partial(render_kept, edge, self.folder)


def render_kept(edge: int, folder: Path | None, source: Path) -> bytes | None:
    """Render a picture at a size, through the cache.

    Args:
        edge: The longer side, in pixels.
        folder: The cache folder, or None.
        source: Image or RAW file.

    Returns:
        The JPEG bytes, or None when the picture cannot be decoded.
    """
    return cached_preview(PreviewJob(source, edge, folder))


def cached_preview(job: PreviewJob) -> bytes | None:
    """Read the preview from the cache, or render it and keep it there.

    Runs in a worker process.

    Args:
        job: The picture, the size and the cache folder.

    Returns:
        The JPEG bytes, or None when the picture cannot be decoded.
    """
    if job.folder is None:
        return jpeg_preview(job.source, job.edge)
    try:
        version = job.source.stat()
    except OSError:
        return None
    target = job.folder / preview_key(job, version.st_size, version.st_mtime_ns)
    with contextlib.suppress(OSError):
        kept = target.read_bytes()
        os.utime(target)  # used now: trimmed last
        return kept or None  # empty: this version cannot be shown
    image = jpeg_preview(job.source, job.edge)
    keep_preview(target, image or b"")
    return image


def preview_key(job: PreviewJob, size: int, mtime_ns: int) -> str:
    """Name the preview of one version of a file at one size.

    Args:
        job: The picture and the size.
        size: The file's size, in bytes.
        mtime_ns: Its modification time.

    Returns:
        A file name such as `0f3a….jpg`.
    """
    version = _VIDEO_VERSION if media_kind(job.source) is MediaKind.VIDEO else _VERSION
    key = f"{version}\0{job.source}\0{size}\0{mtime_ns}\0{job.edge}"
    return hashlib.sha256(key.encode()).hexdigest()[:_NAME_LENGTH] + _SUFFIX


def keep_preview(target: Path, image: bytes) -> None:
    """Write a preview whole, or not at all.

    Args:
        target: Its place in the cache.
        image: The JPEG bytes; empty when the picture cannot be shown.
    """
    partial_file = target.with_name(f"{target.name}.{os.getpid()}{_PARTIAL}")
    with contextlib.suppress(OSError):
        target.parent.mkdir(parents=True, exist_ok=True)
        partial_file.write_bytes(image)
        partial_file.replace(target)


def trim_previews(folder: Path | None, budget: int) -> int:
    """Keep the cache folder within its bound, the previews used least recently first.

    Args:
        folder: The cache folder of previews, or None.
        budget: The bound, in bytes.

    Returns:
        How many previews were removed.
    """
    if folder is None:
        return 0
    try:
        kept = [
            (stat.st_mtime_ns, stat.st_size, path)
            for path in folder.iterdir()
            if path.is_file() and (stat := path.stat())
        ]
    except OSError:
        return 0
    total = sum(size for _used, size, _path in kept)
    if total <= budget:
        return 0
    removed = 0
    for _used, size, path in sorted(kept):
        if total <= budget * _TRIMMED_SHARE:
            break
        with contextlib.suppress(OSError):
            path.unlink()
            total -= size
            removed += 1
    return removed
