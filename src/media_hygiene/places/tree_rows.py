r"""Every folder of the index, as `browse` shows them: any of them can be placed (0242).

A folder such as `Mariage Julie`, named after no town, is placed from the map's
"Any folder" list: each folder of the index's tree (`search/folder_tree`, the disk is
not walked) with its photos and videos without GPS, its subfolders included, the ones
a position helps. Saved, it is a `[[places.folders]]` row like a town folder's.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.places.clusters import MEMBERS_KEPT, SHOWN
from media_hygiene.places.drawer_rows import Shown
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.models import MediaFile
from media_hygiene.search.folder_tree import folder_counts

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.xmp_towns import IndexedInputs


@dataclass(frozen=True, slots=True)
class TreeRow:
    """One folder of the tree: its host path, its parent's, its name, what lacks GPS."""

    folder: str  # host path
    parent: str | None  # None: a mounted folder, at the top
    name: str
    count: int  # photos and videos without a position, its subfolders included
    videos: int


def tree_rows(
    inputs: IndexedInputs, roots: tuple[Path, ...], mapper: HostPathMapper
) -> tuple[TreeRow, ...]:
    """List every folder under the mounted ones, by path.

    Args:
        inputs: Every file of the index and the positions.
        roots: The mounted folders, in the container.
        mapper: Turns a folder into the host path the user knows.

    Returns:
        The rows, a parent before its subfolders.
    """
    every = folder_counts(((str(file.path), file.size) for file in inputs.files), roots)
    alone = folder_counts(
        (
            (str(file.path), file.size)
            for file in inputs.files
            if file.path not in inputs.points
        ),
        roots,
    )
    tops = {str(root) for root in roots}
    rows: list[TreeRow] = []
    for folder in sorted(every):
        count = alone.get(folder)
        top = folder in tops
        path = Path(folder)
        rows.append(
            TreeRow(
                mapper.to_host(path),
                None if top else mapper.to_host(path.parent),
                mapper.to_host(path) if top else path.name,
                count.photos + count.videos if count else 0,
                count.videos if count else 0,
            )
        )
    return tuple(rows)


def tree_json(rows: Iterable[TreeRow]) -> list[dict[str, object]]:
    """Write the tree for the page; a line's rank is the one `GET /api/tree/` names.

    Args:
        rows: The folders.

    Returns:
        Each folder's rank, host path, parent, name and its files without GPS.
    """
    return [
        {
            "rank": rank,
            "folder": row.folder,
            "parent": row.parent,
            "name": row.name,
            "count": row.count,
            "videos": row.videos,
        }
        for rank, row in enumerate(rows)
    ]


def first_unlocated(
    paths: Iterable[Path], files: Mapping[Path, MediaInput]
) -> tuple[Shown, ...]:
    """The first pictures, then the first videos, a drawer shows of these files.

    Args:
        paths: The files without a position, in their order.
        files: Every file of the index, by path.

    Returns:
        At most `MEMBERS_KEPT` pictures with a preview and as many videos.
    """
    pictures: list[Shown] = []
    videos: list[Shown] = []
    for path in paths:
        kind = media_kind(path)
        if kind is None or (kind is not MediaKind.VIDEO and kind not in SHOWN):
            continue
        kept = videos if kind is MediaKind.VIDEO else pictures
        if len(kept) < MEMBERS_KEPT:
            file = files[path]
            kept.append(Shown(MediaFile(path, file.size, file.mtime_ns, kind)))
    return (*pictures, *videos)


def unlocated_below(inputs: IndexedInputs, folder: Path) -> Iterable[Path]:
    """The files without a position in a folder or its subfolders, by path.

    Args:
        inputs: Every file of the index and the positions.
        folder: The folder, in the container.

    Returns:
        Them, sorted: a drawer keeps only the first ones.
    """
    return sorted(
        file.path
        for file in inputs.files
        if file.path not in inputs.points and file.path.is_relative_to(folder)
    )
