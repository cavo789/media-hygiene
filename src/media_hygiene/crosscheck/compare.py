"""Compare two duplicate finders group by group, explaining the expected differences.

Czkawka may group files media-hygiene deliberately leaves out: another extension, an
excluded folder, a broken file. Those are set aside and counted as *explained*; what
remains must match group for group, or it is a real disagreement to look at. Files
removed since Czkawka ran (by a clean, by hand) make its results outdated: ignored.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import is_within

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Mapping
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.crosscheck.czkawka import Group
    from media_hygiene.scan.filters import ScanFilters


class OutsideReason(StrEnum):
    """Why media-hygiene does not analyse a file Czkawka grouped."""

    NOT_MOUNTED = "not-mounted"
    EXTENSION = "extension"
    EXCLUDED = "excluded"
    BROKEN = "broken"
    GONE = "gone"


@dataclass(frozen=True, slots=True)
class AnalysedScope:
    """What media-hygiene analysed in this run."""

    roots: tuple[Path, ...]
    filters: ScanFilters
    broken: frozenset[Path]
    # Every media path the walk listed; None when unknown (nothing counts as gone).
    listed: frozenset[Path] | None = None
    # Whether a skipped folder still exists: Czkawka may have looked in a deleted one.
    folder_exists: Callable[[Path], bool] = lambda _folder: True

    def outside(self, path: Path) -> OutsideReason | None:
        """Tell why a file is out of media-hygiene's scope, if it is.

        Args:
            path: A container path reported by Czkawka.

        Returns:
            The reason, or None when media-hygiene analysed the file.
        """
        if not any(is_within(path, root) for root in self.roots):
            return OutsideReason.NOT_MOUNTED
        if not self.filters.accepts(path):
            return OutsideReason.EXTENSION
        if (folder := self.skipping(path)) is not None:
            exists = self.folder_exists(folder)
            return OutsideReason.EXCLUDED if exists else OutsideReason.GONE
        if path in self.broken:
            return OutsideReason.BROKEN
        if self.listed is not None and path not in self.listed:
            return OutsideReason.GONE
        return None

    def skipping(self, path: Path) -> Path | None:
        """Find the folder that keeps a file out of the analysis, if any.

        Args:
            path: A container path.

        Returns:
            The outermost folder never analysed (system, trash, excluded) above it.
        """
        return next(
            (
                folder
                for folder in reversed(path.parents)
                if self.filters.skips_dir(folder)
            ),
            None,
        )


@dataclass(frozen=True, slots=True)
class CrossCheckResult:
    """Where the two tools agree, where they differ, and why."""

    ours: tuple[Group, ...]
    theirs: tuple[Group, ...]
    only_ours: tuple[Group, ...]
    only_theirs: tuple[Group, ...]
    outside: Mapping[OutsideReason, int]
    results_date: datetime | None = None
    # The folders never analysed that Czkawka's files are in, with their file count.
    skipped_folders: Mapping[Path, int] = field(default_factory=dict)

    @property
    def agrees(self) -> bool:
        """Tell whether every group in scope is the same in both tools.

        Returns:
            True when no group is found by one tool only.
        """
        return not self.only_ours and not self.only_theirs

    @property
    def outdated(self) -> bool:
        """Tell whether files Czkawka grouped were removed since it ran.

        Returns:
            True when its results are older than the folders: not worth comparing.
        """
        return OutsideReason.GONE in self.outside

    @property
    def copies(self) -> int:
        """Extra copies media-hygiene found (files per group, minus the one kept).

        Returns:
            The count.
        """
        return sum(len(group) - 1 for group in self.ours)


def compare(
    ours: Iterable[Group],
    theirs: Iterable[Group],
    scope: AnalysedScope,
) -> CrossCheckResult:
    """Compare media-hygiene's groups with Czkawka's, out-of-scope files set aside.

    Args:
        ours: media-hygiene's duplicate groups.
        theirs: Czkawka's duplicate groups.
        scope: What media-hygiene analysed.

    Returns:
        The comparison.
    """
    outside: Counter[OutsideReason] = Counter()
    skipped: Counter[Path] = Counter()
    in_scope: list[Group] = []
    for group in theirs:
        kept: list[Path] = []
        for path in group:
            reason = scope.outside(path)
            if reason is None:
                kept.append(path)
                continue
            outside[reason] += 1
            if reason is OutsideReason.EXCLUDED and (folder := scope.skipping(path)):
                skipped[folder] += 1
        if len(kept) > 1:
            in_scope.append(frozenset(kept))
    ours_set, theirs_set = frozenset(ours), frozenset(in_scope)
    return CrossCheckResult(
        ours=tuple(ours_set),
        theirs=tuple(theirs_set),
        only_ours=_sorted(ours_set - theirs_set),
        only_theirs=_sorted(theirs_set - ours_set),
        outside=dict(outside),
        skipped_folders=dict(skipped.most_common()),
    )


def _sorted(groups: Iterable[Group]) -> tuple[Group, ...]:
    """Order groups by their first path, for a stable display.

    Args:
        groups: Groups of paths.

    Returns:
        The groups, sorted.
    """
    return tuple(sorted(groups, key=lambda group: sorted(map(str, group))))
