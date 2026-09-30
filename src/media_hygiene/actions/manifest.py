"""Prove a sort lost nothing: count the files before and after, check every move.

The census walks the source roots and the target roots (junk files apart: they may go
to the quarantine). Every file moved must be at its target with its size, and with its
SHA-256 when it crossed disks. The result is shown, and written as `manifest.json`.
"""

from __future__ import annotations

import os
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable

    from media_hygiene.actions.journal import JournalEntry


class Census(BaseModel):
    """How many files, and bytes, the roots hold."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    files: int = 0
    bytes: int = 0


class Manifest(BaseModel):
    """The proof of one sort run, written to its report folder."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run_id: str
    plan_id: str
    roots: tuple[str, ...]  # host paths
    before: Census
    after: Census
    moved: int
    verified: int
    problems: tuple[str, ...] = ()

    @property
    def intact(self) -> bool:
        """Tell whether nothing was lost.

        Returns:
            True when the counts are equal and every move is verified.
        """
        return self.before == self.after and not self.problems


def census(roots: Iterable[Path], junk: frozenset[str]) -> Census:
    """Count the files below some folders, each file once, junk files apart.

    Args:
        roots: The folders; one inside another is counted once.
        junk: Casefolded names of junk files.

    Returns:
        The file and byte counts.
    """
    ordered = sorted(set(roots), key=lambda root: len(root.parts))
    outer: list[Path] = []
    for root in ordered:
        if not any(is_within(root, kept) for kept in outer):
            outer.append(root)
    files = size = 0
    for root in outer:
        for folder, _dirs, names in os.walk(root):
            for name in names:
                if name.casefold() in junk:
                    continue
                path = Path(folder, name)
                if path.is_symlink() or not path.is_file():
                    continue
                files += 1
                size += path.stat().st_size
    return Census(files=files, bytes=size)


def verify_moves(
    moved: Iterable[JournalEntry], to_host: Callable[[Path], str]
) -> tuple[int, tuple[str, ...]]:
    """Check each file moved is at its target, whole.

    Args:
        moved: The entries of the moves done.
        to_host: Shows a container path as the user knows it.

    Returns:
        The count verified, and the problems found (host paths).
    """
    verified = 0
    problems: list[str] = []
    for entry in moved:
        target = Path(entry.target or "")
        problem = _move_problem(entry, target)
        if problem is None:
            verified += 1
        else:
            problems.append(f"{to_host(target)}: {problem}")
    return verified, tuple(problems)


def _move_problem(entry: JournalEntry, target: Path) -> str | None:
    """Tell what is wrong with one move.

    Args:
        entry: The move.
        target: Where the file went.

    Returns:
        The translated problem, or None when the file is there, whole.
    """
    if not target.is_file():
        return _("the file moved from {path} is not there").format(path=entry.host_path)
    if target.stat().st_size != entry.size:
        return _("its size changed")
    if entry.sha256 is not None and full_digest(target) != entry.sha256:
        return _("its content changed")
    return None
