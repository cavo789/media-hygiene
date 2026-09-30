"""Source folders a sort left empty: found deepest first, removed, recreated by `undo`.

A folder is empty when nothing is left in it but junk files (`Thumbs.db`...): those go
to the quarantine first. A folder holding anything else stays. The roots, the mount
points, protected and excluded folders are never removed. The same walk predicts, before
anything moves, what the sort will remove.
"""

from __future__ import annotations

import os
from dataclasses import dataclass, field
from enum import Enum, auto
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_names import owners
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.sidecars import is_sidecar

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator


class Fate(Enum):
    """What happens to a folder the sort emptied, or tried to."""

    REMOVED = auto()
    HOLDS_FILES = auto()  # something else than junk files is left
    HOLDS_JUNK = auto()  # only junk is left, and no quarantine to put it in


@dataclass(frozen=True, slots=True)
class FolderRules:
    """Which folders may go, and which files do not keep a folder alive."""

    junk: frozenset[str]  # casefolded names
    stops: frozenset[Path]  # never removed: roots and mount points
    kept: tuple[Path, ...] = ()  # never removed, nor anything below: protected...
    quarantine: bool = True  # junk files can be set aside


@dataclass(frozen=True, slots=True)
class Verdict:
    """A folder, its fate, and the junk files to set aside first."""

    folder: Path
    fate: Fate
    junk: tuple[Path, ...] = ()


@dataclass(slots=True)
class _Walk:
    """What a walk knows: the files about to go, the folders already gone."""

    gone: dict[Path, list[str]] = field(default_factory=dict[Path, list[str]])
    removed: set[Path] = field(default_factory=set[Path])
    kept: set[Path] = field(default_factory=set[Path])


def candidates(sources: Iterable[Path], rules: FolderRules) -> list[Path]:
    """The folders of the files sorted, and their parents up to a root, deepest first.

    Args:
        sources: The files sorted (their paths before the sort).
        rules: The folders never removed.

    Returns:
        The folders that may end up empty.
    """
    found: set[Path] = set()
    for source in sources:
        folder = source.parent
        while folder not in found and _removable(folder, rules):
            found.add(folder)
            folder = folder.parent
    return sorted(found, key=lambda folder: (-len(folder.parts), str(folder)))


def verdicts(
    folders: list[Path], rules: FolderRules, gone: Iterable[Path] = ()
) -> Iterator[Verdict]:
    """Tell, deepest first, which folders are empty but for junk.

    Before a sort, `gone` lists the files about to move: the walk predicts. After it,
    `gone` is empty: the walk reads the disk, and the caller removes each folder before
    the walk looks at its parent.

    Args:
        folders: The candidates, deepest first.
        rules: Junk files, and whether they can be set aside.
        gone: Files (and, by name, their sidecars) about to leave.

    Yields:
        One verdict per candidate that exists.
    """
    walk = _Walk()
    for path in gone:
        walk.gone.setdefault(path.parent, []).append(path.name)
    for folder in folders:
        try:
            with os.scandir(folder) as scanned:
                entries = [Path(entry.path) for entry in scanned]
        except OSError:
            continue
        left = [path for path in entries if not _leaves(path, walk)]
        junk = tuple(path for path in left if path.name.casefold() in rules.junk)
        others = [path for path in left if path not in junk]
        if others:
            walk.kept.add(folder)
            # A parent kept only by a folder kept below it is not told twice.
            if not all(path in walk.kept for path in others):
                yield Verdict(folder, Fate.HOLDS_FILES)
        elif junk and not rules.quarantine:
            walk.kept.add(folder)
            yield Verdict(folder, Fate.HOLDS_JUNK)
        else:
            walk.removed.add(folder)
            yield Verdict(folder, Fate.REMOVED, junk)


def _leaves(path: Path, walk: _Walk) -> bool:
    """Tell whether an entry is gone, or about to be, with its folder or its file.

    Args:
        path: An entry of a candidate folder.
        walk: What the walk knows.

    Returns:
        True for a folder removed, a file about to move, or one of its sidecars.
    """
    if path in walk.removed:
        return True
    names = walk.gone.get(path.parent, [])
    if path.name in names:
        return True
    return is_sidecar(path.name) and bool(owners(path.name, names))


def _removable(folder: Path, rules: FolderRules) -> bool:
    """Tell whether a folder may ever be removed.

    Args:
        folder: A folder.
        rules: The folders never removed.

    Returns:
        False for a root, a mount point, the filesystem root, or a protected folder.
    """
    if folder in rules.stops or folder == folder.parent:
        return False
    return not any(is_within(folder, kept) for kept in rules.kept)


@dataclass(frozen=True, slots=True)
class FolderReport:
    """The folders a sort removed, and those it had to leave."""

    removed: int = 0
    kept: tuple[Verdict, ...] = ()

    @classmethod
    def of(cls, found: Iterable[Verdict]) -> FolderReport:
        """Count verdicts (a prediction, or what was done).

        Args:
            found: The verdicts.

        Returns:
            The removed count and the folders kept.
        """
        listed = list(found)
        return cls(
            sum(1 for verdict in listed if verdict.fate is Fate.REMOVED),
            tuple(verdict for verdict in listed if verdict.fate is not Fate.REMOVED),
        )
