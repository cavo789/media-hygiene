"""What an album run will do: one free name per file, never twice the same file.

The album is flat: each file keeps its name, followed by ` (2)`, ` (3)`... when the
name is taken by another file (names compared case-insensitively, as Windows does). A
file already in the album, under any name, is not linked again: running the same
`album` command twice adds only the new files.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable


@dataclass(frozen=True, slots=True)
class Pick:
    """A file the album gathers, where it is now."""

    source: Path
    size: int
    mtime_ns: int


@dataclass(frozen=True, slots=True)
class AlbumLink:
    """A hard link to make: `link`, a second name of `source`."""

    source: Path
    link: Path
    size: int
    mtime_ns: int


@dataclass(frozen=True, slots=True)
class AlbumPlan:
    """The album folder, the links to make, and the files set aside, with why."""

    folder: Path
    links: tuple[AlbumLink, ...] = ()
    present: tuple[Path, ...] = ()  # in the album already
    missing: tuple[Path, ...] = ()  # neither where the plan nor where a sort put it
    elsewhere: tuple[Path, ...] = ()  # on another disk or mount: no link possible


def plan_links(
    folder: Path, picks: Iterable[Pick], same_mount: Callable[[Path], bool]
) -> AlbumPlan:
    """Give each file a free name in the album, unless it is there already.

    Args:
        folder: The album folder (it may not exist yet).
        picks: The files gathered.
        same_mount: Tells whether a file is on the album's disk and mount.

    Returns:
        The plan; `missing` is left to the caller.
    """
    taken, inside = _contents(folder)
    links: list[AlbumLink] = []
    present: list[Path] = []
    elsewhere: list[Path] = []
    for pick in picks:
        if not same_mount(pick.source):
            elsewhere.append(pick.source)
            continue
        info = pick.source.stat()
        if info.st_ino and (info.st_dev, info.st_ino) in inside:
            present.append(pick.source)
            continue
        name = _free_name(pick.source.name, taken)
        taken.add(name.casefold())
        links.append(AlbumLink(pick.source, folder / name, pick.size, pick.mtime_ns))
    return AlbumPlan(folder, tuple(links), tuple(present), (), tuple(elsewhere))


def _contents(folder: Path) -> tuple[set[str], set[tuple[int, int]]]:
    """Read what the album holds already.

    Args:
        folder: The album folder.

    Returns:
        The names taken (casefolded), and the identities of its files.
    """
    if not folder.is_dir():
        return set(), set()
    names: set[str] = set()
    identities: set[tuple[int, int]] = set()
    with os.scandir(folder) as entries:
        for entry in entries:
            names.add(entry.name.casefold())
            if entry.is_file(follow_symlinks=False):
                info = entry.stat(follow_symlinks=False)
                identities.add((info.st_dev, info.st_ino))  # 0: no identity known
    return names, identities


def _free_name(name: str, taken: set[str]) -> str:
    """The name itself, or with the first free ` (n)` before its extension.

    Args:
        name: The file's name.
        taken: The names used already, casefolded.

    Returns:
        A name not in `taken`.
    """
    if name.casefold() not in taken:
        return name
    path = Path(name)
    number = 2
    while (candidate := f"{path.stem} ({number}){path.suffix}").casefold() in taken:
        number += 1
    return candidate
