"""What `browse` shows of a list of files: photos or videos only, by name, date or size.

Shared by the files of one folder and the heaviest files of the library. The size is
sorted on the byte count, never on the text the page shows; ties go by name.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Literal

from media_hygiene.constants import MediaKind
from media_hygiene.scan.filters import media_kind
from media_hygiene.search.folder_tree import PHOTOS

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

type Order = Literal["name", "date", "size"]
type Shown = Literal["all", "photos", "videos"]  # the page's **Show**
type FileRow = tuple[int, str, int, str | None]  # key, path, size, day


def is_shown(path: Path, shown: Shown) -> bool:
    """Tell whether a file is of the kind the page shows.

    Args:
        path: The file.
        shown: All of them, the photos (RAW included) or the videos.

    Returns:
        True when it is shown.
    """
    if shown == "all":
        return True
    kind = media_kind(path)
    return kind in PHOTOS if shown == "photos" else kind is MediaKind.VIDEO


def ordered(rows: Iterable[FileRow], order: Order) -> list[FileRow]:
    """Sort files as the page asks.

    Args:
        rows: The files.
        order: By name; by date (undated last); by size, the largest first.

    Returns:
        The files, ties broken by name (casefold).
    """
    if order == "date":
        return sorted(rows, key=lambda row: (row[3] is None, row[3] or "", _name(row)))
    if order == "size":
        return sorted(rows, key=lambda row: (-row[2], _name(row)))
    return sorted(rows, key=_name)


def _name(row: FileRow) -> str:
    """The sort key of a file's path.

    Args:
        row: The file.

    Returns:
        Its path, casefolded.
    """
    return row[1].casefold()
