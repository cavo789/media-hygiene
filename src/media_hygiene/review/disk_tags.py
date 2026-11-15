"""The tags of many photos on the disk now, their `stat`s side by side (2026-11-15).

On the maintainer's PC the photos are a Windows folder mounted into the container:
each `stat` waits about 2 ms on the mount, not on the CPU. A grid of 201 photos took
1.4 s with three `stat`s per photo, one after the other (measured, `/person` like);
one per photo, several at once, overlaps those waits.
"""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Final

from media_hygiene.review.versioned import disk_tag

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

# Waits on the mount, not work: more than the cores helps; the mount takes 16 well.
_AT_ONCE: Final = 16


def disk_tags(paths: Iterable[Path]) -> dict[Path, str]:
    """Each photo's tag as it is on the disk now (`disk_tag`), once per photo.

    Args:
        paths: The photos, in the container.

    Returns:
        Tag by path; empty for a file that cannot be read.
    """
    unique = list(dict.fromkeys(paths))
    if len(unique) < 2:  # noqa: PLR2004  # one photo: no thread to start
        return {path: disk_tag(path) for path in unique}
    with ThreadPoolExecutor(max_workers=_AT_ONCE) as pool:
        return dict(zip(unique, pool.map(disk_tag, unique), strict=True))
