r"""List a folder for `mh push`: every file, its size and time, what was unreadable.

Every file counts, not only photos and videos (a PDF in `C:\Photos` is backed up too,
TODO 0264); the folders skipped are the system ones (`#recycle`, `@eaDir`…), the names
of `[scan] excluded_names` and the folders of `[folders] excluded`, the same on both
sides so that a folder skipped on the PC is never taken for gone from the target.
Symbolic links are not followed.
"""

from __future__ import annotations

import os
from dataclasses import dataclass
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING

from media_hygiene.plan.push_entries import Stat

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping


@dataclass(frozen=True, slots=True)
class Listed:
    """The files below a folder, by their path relative to the target."""

    files: Mapping[str, Stat]
    unreadable: tuple[Path, ...] = ()


def list_tree(
    root: Path, prefix: str, skips: Callable[[PurePosixPath], bool]
) -> Listed:
    """List every file below a folder.

    Args:
        root: The folder; missing, it holds nothing.
        prefix: Its path relative to the target (`C/Photos`), put before each file.
        skips: Tells, from a folder's path relative to `root`, whether to skip it.

    Returns:
        The files, keyed `<prefix>/<path below root>`, and the folders or files that
        could not be read.
    """
    found = _Found(prefix, skips)
    if not root.is_dir():
        return Listed(found.files)
    pending = [PurePosixPath()]
    while pending:
        below = pending.pop()
        folder = root / below
        try:
            with os.scandir(folder) as entries:
                items = list(entries)
        except OSError:
            found.unreadable.append(folder)
            continue
        for item in items:
            pending.extend(found.add(item, below))
    return Listed(found.files, tuple(found.unreadable))


class _Found:
    """The files found so far, the folders still to read, what could not be read."""

    def __init__(self, prefix: str, skips: Callable[[PurePosixPath], bool]) -> None:
        """Start empty.

        Args:
            prefix: The folder's path relative to the target.
            skips: Tells whether to skip a folder, by its path below the folder.
        """
        self._prefix = prefix
        self._skips = skips
        self.files: dict[str, Stat] = {}
        self.unreadable: list[Path] = []

    def add(self, item: os.DirEntry[str], below: PurePosixPath) -> list[PurePosixPath]:
        """Keep a file, or say which folder to read next.

        Args:
            item: An entry of the folder `below`.
            below: Its folder, relative to the root.

        Returns:
            The folder to read next, when the entry is one not skipped.
        """
        relative = below / item.name
        try:
            if item.is_dir(follow_symlinks=False):
                return [] if self._skips(relative) else [relative]
            if not item.is_file(follow_symlinks=False):
                return []
            stat = item.stat(follow_symlinks=False)
        except OSError:
            self.unreadable.append(Path(item.path))
            return []
        self.files[f"{self._prefix}/{relative}"] = Stat(stat.st_size, stat.st_mtime_ns)
        return []
