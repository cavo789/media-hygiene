"""How far the sorting is, read from the tree itself (0405): no plan, no journal.

With the convention (0401) a path says its state: `YYYY/YYYY-MM/<name>` is sorted into
an event, a file directly in `YYYY/YYYY-MM` was looked at (nothing special), anything
else is left to do, whoever put it there. It stays true the day media-hygiene is gone,
and a move made in Explorer counts after the next audit. The counts come from the
index alone (its paths, no walk); protected folders, backups and the `[classify]
leave` folders are counted apart, never as "left". The folders left, the largest first,
are the work list. Kept until the index changes: `status` and the home page ask often.
"""

from __future__ import annotations

import sqlite3
from collections import Counter
from dataclasses import dataclass
from functools import lru_cache
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.convention import Place, place_of_path
from media_hygiene.index.listing import every_path
from media_hygiene.index.read_only import connect_read_only

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.services.runtime import Runtime

_KEPT: Final = 2  # versions of the index remembered
_SEPARATOR: Final = "/"  # of container paths


@dataclass(frozen=True, slots=True)
class DiskProgress:
    """The files of the index by state, and the folders still to sort."""

    sorted: int  # in an event folder
    nothing_special: int  # directly in their month folder
    left: int
    kept: int  # protected, backups, `leave`: never to sort
    folders: tuple[tuple[str, int], ...]  # host folder, files left; largest first

    @property
    def total(self) -> int:
        """The files counted, kept ones apart.

        Returns:
            Sorted, nothing special and left.
        """
        return self.sorted + self.nothing_special + self.left


def disk_progress(runtime: Runtime) -> DiskProgress | None:
    """Count the files of the index by what their path says.

    Args:
        runtime: Settings (the folders kept), mount points (host paths), the index.

    Returns:
        The counts; None without a readable index.
    """
    index = runtime.index_file
    if index is None or not index.is_file():
        return None
    settings, mapper = runtime.settings, runtime.mapper
    kept = tuple(
        str(mapper.to_container(folder))
        for folder in (*settings.folders.untouched, *settings.classify.leave)
    )
    try:
        counted = _counted(index, (index.stat().st_mtime_ns, kept))
    except sqlite3.Error:  # an index too old or damaged: `status` says nothing of it
        return None
    folders = tuple((mapper.to_host(Path(f)), n) for f, n in counted.folders)
    return DiskProgress(
        counted.sorted, counted.nothing_special, counted.left, counted.kept, folders
    )


@lru_cache(maxsize=_KEPT)
def _counted(index: Path, key: tuple[int, tuple[str, ...]]) -> DiskProgress:
    """Read the paths of the index once per version of it, and of the folders kept.

    Args:
        index: The index file.
        key: Its modification time, and the folders kept (container paths).

    Returns:
        The counts, the folders in container paths.
    """
    _stamp, kept = key
    connection = connect_read_only(index)
    try:
        return count_paths(every_path(connection), tuple(Path(k) for k in kept))
    finally:
        connection.close()


def count_paths(paths: Iterable[str], kept: tuple[Path, ...]) -> DiskProgress:
    """Count paths by what they say of the sorting.

    Args:
        paths: Container paths of files.
        kept: Folders never sorted.

    Returns:
        The counts; the folders left in container paths, the largest first, then
        by name.
    """
    states: Counter[Place] = Counter()
    left: Counter[str] = Counter()
    kept_files = 0
    prefixes = tuple(str(folder) + _SEPARATOR for folder in kept)
    folders_kept = frozenset(str(folder) for folder in kept)
    for text in paths:  # strings, not `Path`: 70,000 paths in a fraction of a second
        folder = text.rpartition(_SEPARATOR)[0]
        if folder in folders_kept or text.startswith(prefixes):
            kept_files += 1
            continue
        place = Place(place_of_path(text))
        states[place] += 1
        if place is Place.LEFT:
            left[folder] += 1
    folders = tuple(sorted(left.items(), key=lambda item: (-item[1], item[0])))
    return DiskProgress(
        states[Place.EVENT],
        states[Place.NOTHING_SPECIAL],
        states[Place.LEFT],
        kept_files,
        folders,
    )
