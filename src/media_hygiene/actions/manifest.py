"""Prove a sort lost nothing: count the files before and after, check every move.

The census walks the source roots and the target roots (junk files apart: they may go
to the quarantine). Every file moved must be at its target with its size, and with its
SHA-256 when it crossed disks. The result is shown, and written as `manifest.json`.

Both read each file with one `stat`: on Docker Desktop's share of a Windows disk every
call crosses the VM boundary, and 8,000 files counted twice used to cost 48,000 of them.
"""

from __future__ import annotations

import os
import stat
from pathlib import Path
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.i18n import _
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Iterator

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.sort_plan import SortPlan


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
    sizes = [size for root in outer for size in _file_sizes(root, junk)]
    return Census(files=len(sizes), bytes=sum(sizes))


def touched_folders(plan: SortPlan) -> tuple[Path, ...]:
    """The folders a sort of a few rows changes: where its files are, where they go.

    Every move stays inside them, so their census proves nothing was lost as well as
    the whole collection's does, in a fraction of a second instead of half a minute
    (measured on 43,294 files, 2026-10-25: 34.5 s).

    Args:
        plan: The moves.

    Returns:
        The source folders and the target folders.
    """
    sources = {move.source.parent for move in plan.moves}
    return (*sorted(sources), *sorted({group.folder for group in plan.groups}))


def _file_sizes(root: Path, junk: frozenset[str]) -> Iterator[int]:
    """The size of each regular file below a folder, links and junk files apart.

    The folder listing tells files, folders and links apart without a `stat`
    (as `os.walk` does): only the size costs one, `lstat`. A link is neither counted
    nor followed; a folder that cannot be read is skipped, as `os.walk` skips it.

    Args:
        root: The folder.
        junk: Casefolded names of junk files.

    Yields:
        The sizes, in bytes.
    """
    folders = [root]
    while folders:
        try:
            with os.scandir(folders.pop()) as entries:
                listed = list(entries)
        except OSError:
            continue
        for entry in listed:
            if entry.is_dir(follow_symlinks=False):
                folders.append(Path(entry.path))
            elif (
                entry.is_file(follow_symlinks=False)
                and entry.name.casefold() not in junk
            ):
                yield entry.stat(follow_symlinks=False).st_size


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
    try:
        found = target.stat()  # one call: it is there, a file, and its size
    except OSError:
        found = None
    if found is None or not stat.S_ISREG(found.st_mode):
        return _("the file moved from {path} is not there").format(path=entry.host_path)
    if found.st_size != entry.size:
        return _("its size changed")
    if entry.sha256 is not None and full_digest(target) != entry.sha256:
        return _("its content changed")
    return None
