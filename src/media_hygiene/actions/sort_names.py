"""Where each file of a group lands: its sidecars found, a free name, never overwritten.

When a name is taken in the target folder, the whole group gets the same ` (2)` suffix
after its common name: `IMG_1 (2).HEIC`, `IMG_1 (2).MOV`, `IMG_1 (2).xmp`,
`IMG_1 (2).CR2.xmp` still belong together.
"""

from __future__ import annotations

import itertools
import os
from pathlib import Path, PurePath
from typing import TYPE_CHECKING

from media_hygiene.scan.sidecars import is_sidecar

if TYPE_CHECKING:
    from collections.abc import Collection, Iterable

    from media_hygiene.actions.sort_plan import MoveGroup


def owners(sidecar: str, names: Iterable[str]) -> list[str]:
    """The files, among `names`, a sidecar belongs to.

    Args:
        sidecar: A sidecar's name: `IMG_1.xmp` or `IMG_1.CR2.xmp`.
        names: Names of files in its folder.

    Returns:
        Those whose name, or name without extension, is the sidecar's stem.
    """
    key = PurePath(sidecar).stem.casefold()
    return [
        name
        for name in names
        if key in {name.casefold(), PurePath(name).stem.casefold()}
    ]


class SourceSidecars:
    """The sidecars of the source folders, each folder listed once by a sort (0171).

    Listing a folder of 4,000 photos for each of its files made a sort quadratic, on
    a shared folder above all. A sidecar is handed to the first group owning it: it
    moves once.
    """

    def __init__(self) -> None:
        """Start with no folder listed."""
        self._by_folder: dict[Path, dict[str, list[Path]]] = {}

    def take(self, group: MoveGroup) -> list[Path]:
        """Hand out the sidecars next to the files of a group.

        Args:
            group: Files that move together, all in one folder.

        Returns:
            The sidecars belonging to one of them, by name, not handed out before.
        """
        folder = group.moves[0].source.parent
        keyed = self._by_folder.get(folder)
        if keyed is None:
            keyed = self._by_folder[folder] = _sidecars_in(folder)
        found: list[Path] = []
        for move in group.moves:
            name = move.source.name
            for key in (name.casefold(), PurePath(name).stem.casefold()):
                found.extend(keyed.pop(key, ()))
        return sorted(found)


def _sidecars_in(folder: Path) -> dict[str, list[Path]]:
    """List the sidecars of a folder, by the name they belong to.

    Args:
        folder: A source folder.

    Returns:
        Casefolded stem of each sidecar (`IMG_1` or `IMG_1.CR2`) → the sidecars.
    """
    keyed: dict[str, list[Path]] = {}
    try:
        with os.scandir(folder) as entries:
            for entry in entries:
                if entry.is_file() and is_sidecar(entry.name):
                    key = PurePath(entry.name).stem.casefold()
                    keyed.setdefault(key, []).append(Path(entry.path))
    except OSError:
        return {}
    return keyed


def free_names(
    folder: Path, names: list[str], given: Collection[str] = frozenset()
) -> dict[str, str]:
    """Give each name of a group a name free in the target folder, the same suffix.

    Args:
        folder: The target folder (it may not exist yet).
        names: The names of the group, the leading file first.
        given: Names (casefolded) already given in `folder` to files of the run not
            moved yet: free on the disk, taken all the same.

    Returns:
        Name → the name it takes in `folder`.
    """
    stem = PurePath(names[0]).stem
    for number in itertools.count(1):
        taken = {name: numbered(name, stem, number) for name in names}
        if not any(
            name.casefold() in given or os.path.lexists(folder / name)
            for name in taken.values()
        ):
            return taken
    return {}  # pragma: no cover - `itertools.count` never ends


def numbered(name: str, stem: str, number: int) -> str:
    """Add ` (n)` after the common name of a group; the first number adds nothing.

    Args:
        name: A file name.
        stem: The common name of its group.
        number: 1, 2, 3...

    Returns:
        `IMG_1 (2).CR2.xmp` for `IMG_1.CR2.xmp`, `IMG_1` and 2.
    """
    if number == 1:
        return name
    if not name.casefold().startswith(stem.casefold()):
        stem = PurePath(name).stem
    return f"{name[: len(stem)]} ({number}){name[len(stem) :]}"
