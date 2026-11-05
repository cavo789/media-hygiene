"""The folders a phone can show on the TV, the most recent photos first (0507).

One query groups the index's files by folder with their newest date; the phone shows
each folder's last part, its full name kept as the value matched by `/choose`.
"""

from __future__ import annotations

from collections import Counter
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.search.days import NAME as DAY

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

# Each folder holding files, with its newest day and its newest mtime: one query.
_PARENT: Final = "rtrim(path, replace(path, '/', ''))"  # up to the last `/`, kept
_FOLDERS: Final = (
    f"SELECT {_PARENT} AS folder, MAX({DAY}(media_date)), MAX(mtime_ns)"  # noqa: S608
    " FROM files GROUP BY folder"
)


def newest_first(runtime: Runtime, search: SearchIndex) -> list[tuple[str, Path]]:
    """The folders holding files of the index, the most recent photos first (0507).

    By the newest date the audit read among its files; a folder without any date
    after, by its newest file change; then by name.

    Args:
        runtime: Settings, mount points and the host mapper.
        search: The open index.

    Returns:
        Each folder's name as the Explorer shows it, and the folder in the container.
    """
    data = runtime.locations.data_dir
    found: list[tuple[bool, str, int, str, Path]] = []
    for text, day, mtime in search.connection.execute(_FOLDERS):
        folder = Path(text.rstrip("/") or "/")
        if folder.is_relative_to(data):
            name = runtime.mapper.to_host(folder)
            found.append((day is None, day or "", mtime or 0, name, folder))
    found.sort(key=lambda row: (row[0], _reversed(row[1]), -row[2], row[3].casefold()))
    return [(name, folder) for _undated, _day, _mtime, name, folder in found]


def _reversed(day: str) -> tuple[int, ...]:
    """A day as a key sorting the newest first.

    Args:
        day: `YYYY-MM-DD`, or empty.

    Returns:
        The negated code points.
    """
    return tuple(-ord(each) for each in day)


def labelled(folders: list[tuple[str, Path]]) -> list[tuple[str, str]]:
    """A short label for each folder, readable on a phone: its last part.

    Two folders with the same last part get their parent's too.

    Args:
        folders: The folders' names as the Explorer shows them, and their paths.

    Returns:
        Each name, and its label.
    """
    tails = [_tail(name, 1) for name, _folder in folders]
    counted = Counter(tails)
    twice = {tail for tail, times in counted.items() if times > 1}
    return [
        (name, _tail(name, 2) if tail in twice else tail)
        for (name, _folder), tail in zip(folders, tails, strict=True)
    ]


def _tail(name: str, parts: int) -> str:
    """The last parts of a Windows or Linux path, as written.

    Args:
        name: The path.
        parts: How many parts.

    Returns:
        Those parts, joined by the path's own separator.
    """
    separator = "\\" if "\\" in name else "/"
    return separator.join(name.rstrip(separator).split(separator)[-parts:])
