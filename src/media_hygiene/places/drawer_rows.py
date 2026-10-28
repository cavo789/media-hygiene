r"""The files of the map page's drawer, grouped by folder (0232, 0233).

A cluster's or a folder's files reach the page as one list: the largest folder first,
each file with its folder as the user knows it (`C:\Photos\2014\Geer`), the folder's
name often naming the place. A picture gets a preview for the grid and a larger one
for the viewer; a video is listed by name. A file moved since the audit keeps its
place in its folder, as not found.
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.review.views import PREVIEW_LINK, preview_key

if TYPE_CHECKING:
    from collections.abc import Iterable, MutableMapping
    from pathlib import Path

    from media_hygiene.geo.distance import Point
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.models import MediaFile

JPEG: Final = ".jpg"
LARGE_PREFIX: Final = "/large/"  # the viewer's preview, larger than the grid's


@dataclass(frozen=True, slots=True)
class Shown:
    """A file of the drawer, and where it was taken (None: no position)."""

    file: MediaFile
    point: Point | None = None


def drawer_rows(
    shown: Iterable[Shown],
    mapper: HostPathMapper,
    sources: MutableMapping[str, Path],
) -> list[dict[str, object]]:
    """List the files for the page, grouped by folder, the largest folder first.

    Args:
        shown: The files, in the order they are listed within their folder.
        mapper: Turns a folder into the host path the user knows.
        sources: Where each preview key listed is recorded, to serve it later.

    Returns:
        Each file's name, host folder, whether it is a video and still there; a
        picture's previews, a located file's position.
    """
    groups: defaultdict[Path, list[Shown]] = defaultdict(list)
    for item in shown:
        groups[item.file.path.parent].append(item)
    ordered = sorted(groups.items(), key=lambda group: (-len(group[1]), str(group[0])))
    return [
        _row(item, mapper.to_host(folder), sources)
        for folder, items in ordered
        for item in items
    ]


def _row(
    item: Shown, folder: str, sources: MutableMapping[str, Path]
) -> dict[str, object]:
    """Describe one file.

    Args:
        item: The file and its position.
        folder: Its folder, as a host path.
        sources: Where its preview key is recorded.

    Returns:
        The row.
    """
    file = item.file
    video = file.kind is MediaKind.VIDEO
    row: dict[str, object] = {
        "name": file.path.name,
        "folder": folder,
        "video": video,
        "found": file.path.is_file(),
    }
    if not video:
        key = preview_key(file)
        sources[key] = file.path
        row["preview"] = f"{PREVIEW_LINK}{key}{JPEG}"
        row["large"] = f"{LARGE_PREFIX.removeprefix('/')}{key}{JPEG}"
    if item.point is not None:
        row["latitude"] = item.point.latitude
        row["longitude"] = item.point.longitude
    return row
