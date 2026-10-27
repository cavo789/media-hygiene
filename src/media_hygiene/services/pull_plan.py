r"""What `mh pull` would copy back from the target of `mh push` (0376).

Pure planning, no file read: the target and the photo folders are listed by the
caller (`push_listing.list_tree`), both keyed by the path relative to the target
(`C/Photos/2019/a.jpg`). A file is copied back only when its place on the PC is free:
nothing on the PC is ever replaced, nothing in the target is ever written. The files
of `.removed` (deleted on purpose before a push) never come back; a file whose
content the index already knows elsewhere in the folders (moved by `sort`, `clean`
or the user since the push) is not copied a second time.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.services.push_place import REMOVED_FOLDER

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.plan.push_entries import Stat


@dataclass(frozen=True, slots=True)
class PullSides:
    """The two listings and what the index knows of the contents.

    Attributes:
        target: The target's files, `.removed` included, by relative path.
        pc: The photo folders' files, by the same relative path.
        digests: The SHA-256 the index knows of a target file, by relative path
            (the row of its place at the last push), when it knows one.
        present: The SHA-256 of the files now in the photo folders.
    """

    target: Mapping[str, Stat]
    pc: Mapping[str, Stat]
    digests: Mapping[str, str] = field(default_factory=dict)
    present: frozenset[str] = frozenset()


@dataclass(frozen=True, slots=True)
class PullPlan:
    """The files to copy back and those left out, each sorted by path.

    Attributes:
        copies: Missing at their place on the PC: copied back.
        kept: Present on the PC with another size or time: left alone.
        moved: Missing at their place, but their content is elsewhere: left out.
        removed: Files of `.removed`: deleted on purpose, never back.
    """

    copies: tuple[str, ...]
    kept: tuple[str, ...]
    moved: tuple[str, ...]
    removed: tuple[str, ...]


def plan_pull(sides: PullSides, folders: frozenset[str] = frozenset()) -> PullPlan:
    """Sort the target's files into copied back, left alone, moved, removed.

    Args:
        sides: The listings and the index's digests.
        folders: The relative folders to restore (`C/Photos`); empty: every one.

    Returns:
        The plan.
    """
    copies: list[str] = []
    kept: list[str] = []
    moved: list[str] = []
    removed: list[str] = []
    for path in sorted(sides.target):
        if path.split("/", 1)[0] == REMOVED_FOLDER:
            removed.append(path)
        elif not _chosen(path, folders):
            continue
        elif (here := sides.pc.get(path)) is not None:
            if not here.same(sides.target[path]):
                kept.append(path)
        elif sides.digests.get(path) in sides.present:
            moved.append(path)
        else:
            copies.append(path)
    return PullPlan(tuple(copies), tuple(kept), tuple(moved), tuple(removed))


def copied_size(plan: PullPlan, target: Mapping[str, Stat]) -> int:
    """The bytes a plan copies back.

    Args:
        plan: The plan.
        target: The target's listing it was made from.

    Returns:
        The sum of the sizes of its copies.
    """
    return sum(target[path].size for path in plan.copies)


def _chosen(path: str, folders: frozenset[str]) -> bool:
    """Tell whether a path is below one of the folders to restore.

    Args:
        path: A relative path.
        folders: The folders; empty: every one.

    Returns:
        True when chosen.
    """
    if not folders:
        return True
    folded = path.casefold()
    return any(folded.startswith(f"{folder.casefold()}/") for folder in folders)
