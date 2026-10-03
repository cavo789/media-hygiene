r"""Detect a tool folder (quarantine, journal, cache, reports) mixed with the photos.

`-v "C:\Photos\quarantine:/quarantine"` next to `-v "C:\Photos:/data/c/Photos"` puts the
quarantine inside a folder to analyse: the audit would read the files set aside, a
sort could move them out again. The other way round, a folder to analyse inside the
quarantine would be emptied by `purge`. Both are found here, by container path and by
host folder.

A tool folder inside an excluded folder (`[folders] excluded`) is never read: allowed.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.paths.host_folders import locate

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.paths.mounts import MountTable


@dataclass(frozen=True, slots=True)
class ToolOverlap:
    """A tool folder and a folder to analyse, one inside the other."""

    kind: MountKind
    tool: Path
    data: Path


@dataclass(frozen=True, slots=True)
class DataScope:
    """The folders to analyse, those excluded, the mount table telling their hosts."""

    table: MountTable
    roots: tuple[Path, ...]
    excluded: tuple[Path, ...] = ()


def tool_overlaps(
    scope: DataScope, tools: Iterable[tuple[MountKind, Path]]
) -> tuple[ToolOverlap, ...]:
    """List the tool folders that are, contain or lie inside a folder to analyse.

    Args:
        scope: The folders to analyse.
        tools: Each tool folder, with its kind.

    Returns:
        One overlap per tool folder and folder to analyse, in the given order.
    """
    return tuple(
        ToolOverlap(kind, tool, root)
        for kind, tool in tools
        for root in scope.roots
        if _overlap(scope, tool, root)
    )


def _overlap(scope: DataScope, tool: Path, root: Path) -> bool:
    """Tell whether a tool folder and a folder to analyse overlap.

    Args:
        scope: The folders to analyse.
        tool: The tool folder.
        root: One folder to analyse.

    Returns:
        True when one is inside the other, unless the tool folder is excluded.
    """
    if tool.is_relative_to(root):
        return not _excluded(scope, tool)
    if root.is_relative_to(tool):
        return True
    host_tool = locate(scope.table.host_folders, tool)
    host_root = locate(scope.table.host_folders, root)
    if host_tool is None or host_root is None:
        return False
    if host_root.contains(host_tool):
        return not _excluded(scope, root.joinpath(*host_tool.relative_to(host_root)))
    return host_tool.contains(host_root)


def _excluded(scope: DataScope, path: Path) -> bool:
    """Tell whether a path lies in an excluded folder, never read.

    Args:
        scope: The folders to analyse.
        path: A container path under a folder to analyse.

    Returns:
        True when an excluded folder holds it.
    """
    return any(path.is_relative_to(folder) for folder in scope.excluded)
