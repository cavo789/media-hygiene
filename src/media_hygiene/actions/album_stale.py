"""The links of an album whose photo was taken out of it since (0374).

A name in the album folder is a link of the album while another name of the same file
(same disk, same inode) lies in the analysed folders: that other name is found through
the index (a file of the same size, then its identity). Only such a name is ever
removed: a file with a single name (copied into the folder by hand: its only copy), or
whose other name is not found (outside the analysed folders), is left in place. `undo`
links the name again from that other name.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ALBUM_MARKER

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from media_hygiene.actions.album_plan import Pick

_ONLY_NAME: Final = 1  # a file with one name: a copy made by hand, its only copy


@dataclass(frozen=True, slots=True)
class StaleLink:
    """A name of the album (`link`) whose photo, at `other`, left the album."""

    link: Path
    other: Path
    size: int
    mtime_ns: int


@dataclass(frozen=True, slots=True)
class Leftovers:
    """The names of the folder no longer in the album: to remove, and left in place."""

    stale: tuple[StaleLink, ...] = ()
    left: tuple[
        Path, ...
    ] = ()  # a link whose other name is outside the analysed folders


def leftovers(
    folder: Path,
    picks: Iterable[Pick],
    other_name: Callable[[os.stat_result], Path | None],
) -> Leftovers:
    """Find the names of the album folder that no file of the album has any more.

    Args:
        folder: The album folder (it may not exist yet).
        picks: The files of the album, where they are now.
        other_name: Finds another name of the same file in the analysed folders.

    Returns:
        The links to remove, and those left in place.
    """
    if not folder.is_dir():
        return Leftovers()
    wanted = {_identity(pick.source) for pick in picks}
    stale: list[StaleLink] = []
    left: list[Path] = []
    with os.scandir(folder) as entries:
        named = sorted(entries, key=lambda entry: entry.name)
    for entry in named:
        if entry.name == ALBUM_MARKER or not entry.is_file(follow_symlinks=False):
            continue
        info = entry.stat(follow_symlinks=False)
        if not info.st_ino or (info.st_dev, info.st_ino) in wanted:
            continue
        if info.st_nlink <= _ONLY_NAME:
            continue
        path = Path(entry.path)
        other = other_name(info)
        if other is None:
            left.append(path)
        else:
            stale.append(StaleLink(path, other, info.st_size, info.st_mtime_ns))
    return Leftovers(tuple(stale), tuple(left))


def _identity(path: Path) -> tuple[int, int]:
    """The disk and inode of a file; (0, 0) when it cannot be read.

    Args:
        path: The file.

    Returns:
        Its identity.
    """
    try:
        info = path.stat()
    except OSError:
        return (0, 0)
    return (info.st_dev, info.st_ino)
