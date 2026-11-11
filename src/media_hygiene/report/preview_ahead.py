"""Make a preview before it is asked for: what the audit prepares for the pages (0674).

Runs in a worker process. A preview already kept is left alone (not even touched:
its place in the least-recently-used order is the pages' business); an empty one
(no picture) is left to `cached_preview`, which tries again once it is old enough.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.report.preview_cache import cached_preview, preview_key

if TYPE_CHECKING:
    from media_hygiene.report.preview_cache import PreviewJob


def made_ahead(job: PreviewJob) -> bool:
    """Render and keep the preview of one file unless it is kept already.

    Args:
        job: The picture, the size and the cache folder (not None).

    Returns:
        True when a thumbnail was made, False when it was kept already, the
        file is gone or it is no picture.
    """
    if job.folder is None:
        return False
    try:
        version = job.source.stat()
    except OSError:
        return False  # gone, or unreadable: the page will say so
    kept = job.folder / preview_key(job, version.st_size, version.st_mtime_ns)
    try:
        if kept.stat().st_size:
            return False
    except OSError:
        pass  # not kept yet
    return cached_preview(job) is not None
