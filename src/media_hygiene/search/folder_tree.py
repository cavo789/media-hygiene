"""The tree of the library's folders, from the index: what `browse` shows on the left.

Each folder counts the photos and videos below it (its subfolders too) and their size,
and how many files lie in it directly. Only the folders under the mounted ones are
listed: the others cannot be shown.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import cache
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_size
from media_hygiene.constants import MediaKind
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.paths.host_paths import HostPathMapper


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

    Text only (0704): each file is added to its own folder, then each folder once to
    those above it; a `Path` per file and per parent took 3 s at 100,000 files.

    Args:
        rows: The path and size of every file of the index.
        roots: The mounted folders, in the container.

    Returns:
        Each folder (container path, as text) and what it holds; the roots first
        listed even when empty.
    """
    counts = {str(root): FolderCount() for root in roots}
    tops = tuple((str(root), str(root).rstrip("/") + "/") for root in roots)
    direct: dict[tuple[str, str], FolderCount] = {}
    for path, size in rows:
        top = next((top for top, inside in tops if path.startswith(inside)), None)
        if top is None:
            continue
        cut = path.rfind("/")
        folder, name = path[:cut], path[cut + 1 :]
        kind = _kind(_suffix(name))
        count = direct.setdefault((top, folder or "/"), FolderCount())
        count.files += 1
        count.size += size
        count.photos += kind in PHOTOS
        count.videos += kind is MediaKind.VIDEO
    for (top, folder), alone in direct.items():
        counts.setdefault(folder, FolderCount()).files += alone.files
        above = folder
        while True:
            count = counts.setdefault(above, FolderCount())
            count.size += alone.size
            count.photos += alone.photos
            count.videos += alone.videos
            if above == top:
                break
            above = above.rpartition("/")[0] or "/"
    return counts


def listed_tree(
    counts: dict[str, FolderCount], mapper: HostPathMapper, roots: tuple[Path, ...]
) -> list[dict[str, object]]:
    """The tree as the page reads it.

    Args:
        counts: What each folder holds (`folder_counts`).
        mapper: Container paths to the host's.
        roots: The mounted folders, in the container.

    Returns:
        The folders, sorted by path, each with its parent, counts and size.
    """
    tops = {str(root) for root in roots}
    return [
        {
            "path": mapper.to_host(Path(folder)),
            "inside": folder,  # container path: the search filters on it (0348)
            "parent": None if folder in tops else mapper.to_host(Path(folder).parent),
            "name": mapper.to_host(Path(folder))
            if folder in tops
            else Path(folder).name,
            "photos": count.photos,
            "videos": count.videos,
            "files": count.files,
            "size": human_size(count.size),
        }
        for folder, count in sorted(counts.items())
    ]


def _suffix(name: str) -> str:
    """A file name's extension, as `Path.suffix` says it.

    Args:
        name: The file name.

    Returns:
        From its last dot past the leading ones, or empty.
    """
    bare = name.lstrip(".")
    dot = bare.rfind(".")
    return bare[dot:] if dot >= 0 else ""


@cache
def _kind(suffix: str) -> MediaKind | None:
    """The media kind of an extension, once per extension.

    Args:
        suffix: The extension.

    Returns:
        What `media_kind` says of it.
    """
    return media_kind(Path(f"file{suffix}"))
