"""Folders a clean leaves empty: predicted before, removed last, recreated by `undo`.

The same walk as `sort` (`sort_folders`): the folders of the files the clean moves or
deletes, and their parents up to a root, deepest first; junk files (`Thumbs.db`...) go
to the quarantine first. Folders empty before the run are never candidates: none of
their files leaves.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_folders import FolderReport, candidates, verdicts

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.sort_folders import FolderRules
    from media_hygiene.plan.models import CleanPlan


@dataclass(frozen=True, slots=True)
class EmptiedFolders:
    """The folders a clean may leave empty, and the rules that keep some."""

    rules: FolderRules
    candidates: tuple[Path, ...] = ()
    gone: tuple[Path, ...] = ()  # the files the clean moves or deletes

    @classmethod
    def of(cls, plan: CleanPlan, rules: FolderRules) -> EmptiedFolders:
        """List the candidates of a plan.

        Args:
            plan: What the clean does.
            rules: The folders never removed, and the junk files.

        Returns:
            The candidates, deepest first.
        """
        gone = sorted(plan.removed | {sidecar.path for sidecar in plan.orphans})
        return cls(rules, tuple(candidates(gone, rules)), tuple(gone))

    def predicted(self) -> FolderReport:
        """Tell, before anything moves, which folders the clean will remove.

        Returns:
            The removed count, and the folders left (junk with no quarantine...).
        """
        return FolderReport.of(verdicts(list(self.candidates), self.rules, self.gone))
