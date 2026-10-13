"""The small previews of a report, rendered in worker processes through the cache."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.constants import Sizes
from media_hygiene.report.preview_cache import PreviewJob, cached_preview

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.report.preview_cache import PreviewPool


@dataclass(frozen=True, slots=True)
class ThumbnailJob:
    """Render `source` as a preview at `target`."""

    source: Path
    target: Path


def make_thumbnail(job: ThumbnailJob, folder: Path | None = None) -> bool:
    """Write a preview, tolerating truncated images (a partial preview helps decide).

    A report gets its own copy: `/reports` and `/cache` are separate mounts.

    Args:
        job: Source image and target file.
        folder: The cache folder of previews, or None.

    Returns:
        True when the preview was written.
    """
    image = cached_preview(PreviewJob(job.source, Sizes.THUMBNAIL_EDGE, folder))
    if image is None:
        return False
    job.target.parent.mkdir(parents=True, exist_ok=True)
    job.target.write_bytes(image)
    return True


async def make_thumbnails(jobs: Sequence[ThumbnailJob], pool: PreviewPool) -> set[Path]:
    """Render every preview in parallel.

    Args:
        jobs: Previews to render.
        pool: The worker pool, and the cache folder.

    Returns:
        The targets actually written.
    """
    loop = asyncio.get_running_loop()
    make = partial(make_thumbnail, folder=pool.folder)
    results = await asyncio.gather(
        *(loop.run_in_executor(pool.executor, make, job) for job in jobs),
    )
    return {job.target for job, written in zip(jobs, results, strict=True) if written}
