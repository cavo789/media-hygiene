"""Many waits on a mounted folder side by side: photos' tags, people's files.

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
    from collections.abc import Callable, Iterable, Sequence
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
    return dict(zip(unique, side_by_side(disk_tag, unique), strict=True))


def side_by_side[T, R](work: Callable[[T], R], items: Sequence[T]) -> list[R]:
    """Run work on each item, several at once: waits on a mounted folder overlap.

    Args:
        work: What to do with one item (reads, writes, `stat`s).
        items: The items.

    Returns:
        Each result, in the order of the items; the first error raised, raised.
    """
    if len(items) < 2:  # noqa: PLR2004  # one item: no thread to start
        return [work(item) for item in items]
    with ThreadPoolExecutor(max_workers=min(_AT_ONCE, len(items))) as pool:
        return list(pool.map(work, items))
