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
    from collections.abc import Iterable

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


def sidecars_of(group: MoveGroup) -> list[Path]:
    """List the sidecars next to the files of a group.

    Args:
        group: Files that move together, all in one folder.

    Returns:
        The sidecars belonging to one of them, by name.
    """
    folder = group.moves[0].source.parent
    names = [move.source.name for move in group.moves]
    try:
        with os.scandir(folder) as entries:
            found = [
                Path(entry.path)
                for entry in entries
                if entry.is_file() and is_sidecar(entry.name)
            ]
    except OSError:
        return []
    return sorted(path for path in found if owners(path.name, names))


def free_names(folder: Path, names: list[str]) -> dict[str, str]:
    """Give each name of a group a name free in the target folder, the same suffix.

    Args:
        folder: The target folder (it may not exist yet).
        names: The names of the group, the leading file first.

    Returns:
        Name → the name it takes in `folder`.
    """
    stem = PurePath(names[0]).stem
    for number in itertools.count(1):
        taken = {name: numbered(name, stem, number) for name in names}
        if not any(os.path.lexists(folder / name) for name in taken.values()):
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
