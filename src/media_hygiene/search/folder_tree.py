"""The tree of the library's folders, from the index: what `browse` shows on the left.

Each folder counts the photos and videos below it (its subfolders too) and their size,
and how many files lie in it directly. Only the folders under the mounted ones are
listed: the others cannot be shown.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Iterable


PHOTOS = frozenset({MediaKind.IMAGE, MediaKind.RAW})


@dataclass(slots=True)
class FolderCount:
    """What a folder holds, its subfolders included; `files`: directly in it."""

    photos: int = 0
    videos: int = 0
    size: int = 0
    files: int = 0


def folder_counts(
    rows: Iterable[tuple[str, int]], roots: tuple[Path, ...]
) -> dict[str, FolderCount]:
    """Count the files of each folder under the mounted ones.

    Args:
        rows: The path and size of every file of the index.
        roots: The mounted folders, in the container.

    Returns:
        Each folder (container path, as text) and what it holds; the roots first
        listed even when empty.
    """
    counts = {str(root): FolderCount() for root in roots}
    tops = tuple(root for root in roots)
    for path, size in rows:
        file = Path(path)
        top = next((root for root in tops if file.is_relative_to(root)), None)
        if top is None or file == top:
            continue
        kind = media_kind(file)
        folder = file.parent
        counts.setdefault(str(folder), FolderCount()).files += 1
        for above in (folder, *folder.parents):
            count = counts.setdefault(str(above), FolderCount())
            count.size += size
            count.photos += kind in PHOTOS
            count.videos += kind is MediaKind.VIDEO
            if above == top:
                break
    return counts
