"""The plan `clean` executes, as immutable value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.plan.keep_decision import KeepDecision
from media_hygiene.plan.similar_models import SimilarFindings
from media_hygiene.scan.inventory import Inventory

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.plan.backups import BackupCoverage
    from media_hygiene.plan.gone import GoneAnswer
    from media_hygiene.plan.returned import ReturnedFile
    from media_hygiene.plan.similar_models import BurstChoice, NearDecision
    from media_hygiene.scan.models import BrokenFile, DuplicateGroup, MediaFile
    from media_hygiene.scan.read_errors import UnreadFile
    from media_hygiene.scan.sidecars import Sidecar
    from media_hygiene.scan.stopwatch import StageTime

# `KeepDecision` lives in `keep_decision` (this module's size), imported from here too.
__all__ = ["AuditFindings", "CleanPlan", "KeepDecision"]


@dataclass(frozen=True, slots=True)
class CleanPlan:  # pylint: disable=too-many-instance-attributes
    """Everything `clean` would do, computed by `audit`."""

    decisions: tuple[KeepDecision, ...]
    broken: tuple[BrokenFile, ...]
    protected_broken: tuple[BrokenFile, ...] = ()
    near: tuple[NearDecision, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    bursts: tuple[BurstChoice, ...] = ()
    delete_copies: bool = False  # `clean --delete`: exact copies deleted, not moved
    chosen: tuple[MediaFile, ...] = ()  # set aside in `search` (`clean --decisions`)
    unwanted: tuple[MediaFile, ...] = ()  # set aside in `review --junk`
    returned: tuple[ReturnedFile, ...] = ()  # set aside before, back (0216)
    gone: tuple[GoneAnswer, ...] = ()  # answered in `review --gone` (0224)

    @property
    def removable_count(self) -> int:
        """Number of duplicate copies `clean` would delete.

        Returns:
            The count.
        """
        return sum(len(decision.removable) for decision in self.decisions)

    @property
    def moved_copies(self) -> int:
        """Number of exact copies moved to the quarantine rather than deleted.

        Returns:
            Every copy by default; with `--delete`, the copies of other files (not
            media) only.
        """
        return sum(
            self.to_quarantine(file)
            for decision in self.decisions
            for file in decision.removable
        )

    def to_quarantine(self, file: MediaFile) -> bool:
        """Tell whether `clean` moves a duplicate copy to the quarantine.

        Args:
            file: A copy to remove.

        Returns:
            True unless `--delete` deletes it (a media copy); another file always goes.
        """
        return file.kind is MediaKind.OTHER or not self.delete_copies

    @property
    def reclaimable(self) -> int:
        """Bytes freed by deleting the duplicate copies.

        Returns:
            The byte count.
        """
        return sum(decision.reclaimable for decision in self.decisions)

    @property
    def broken_size(self) -> int:
        """Bytes of broken files `clean` would quarantine or delete.

        Returns:
            The byte count.
        """
        return sum(item.file.size for item in self.broken)

    @property
    def is_empty(self) -> bool:
        """Tell whether there is nothing to clean.

        Returns:
            True when no duplicate copy, near duplicate, burst shot or file set
            aside, broken file or orphan sidecar is actionable.
        """
        moved = self.near_count or self.burst_count or self.chosen or self.unwanted
        moved = moved or self.orphans
        journal = bool(self.returned or self.gone)
        return not (self.removable_count or self.broken or moved or journal)

    @property
    def near_count(self) -> int:
        """Number of near duplicates to move to the quarantine (`--tier near` only).

        Returns:
            The count.
        """
        return sum(len(decision.removable) for decision in self.near)

    @property
    def burst_count(self) -> int:
        """Number of burst shots a review set aside (`clean --decisions`).

        Returns:
            The count.
        """
        return sum(len(choice.discarded) for choice in self.bursts)

    @property
    def orphans(self) -> tuple[MediaFile, ...]:
        """Sidecars the plan leaves without any file of their name: moved too.

        Returns:
            Their files, in the order of `sidecars`.
        """
        removed = self.removed
        return tuple(s.file for s in self.sidecars if s.is_orphan_without(removed))

    @property
    def removed(self) -> frozenset[Path]:
        """Files the plan deletes or moves, sidecars aside.

        Returns:
            Their paths.
        """
        exact = {file.path for group in self.decisions for file in group.removable}
        near = {file.path for group in self.near for file in group.removable}
        bursts = {file.path for choice in self.bursts for file in choice.discarded}
        broken = {item.file.path for item in self.broken}
        chosen = {file.path for file in (*self.chosen, *self.unwanted)}
        back = {item.file.path for item in self.returned}
        return frozenset(exact | near | bursts | broken | chosen | back)


@dataclass(frozen=True, slots=True)
class AuditFindings:  # pylint: disable=too-many-instance-attributes
    """Result of an audit: how much was scanned, the groups found, and the plan."""

    roots: tuple[Path, ...]
    plan: CleanPlan
    seconds: float = 0.0
    folder_files: Mapping[Path, int] = field(
        default_factory=lambda: MappingProxyType({})
    )
    groups: tuple[DuplicateGroup, ...] = ()
    similar: SimilarFindings = field(default_factory=SimilarFindings)
    inventory: Inventory = field(default_factory=Inventory)
    # Every media path the walk listed, hard-link aliases included; None when unknown.
    listed: frozenset[Path] | None = None
    # How long each stage took, in the order they ran (`audit -v`).
    stages: tuple[StageTime, ...] = ()
    unread: tuple[UnreadFile, ...] = ()  # read again next time, never in the plan
    gone: int = 0  # files gone since, waiting for `review --gone` (0224)
    backups: tuple[BackupCoverage, ...] = ()  # each backup folder compared (0204)

    @property
    def files_scanned(self) -> int:
        """How many media files the audit analysed.

        Returns:
            The files of every folder.
        """
        return sum(self.folder_files.values())
