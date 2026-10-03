"""The plan `clean` executes, as immutable value objects."""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind
from media_hygiene.plan.similar_models import SimilarFindings
from media_hygiene.scan.inventory import Inventory

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.constants import KeepReason
    from media_hygiene.plan.similar_models import BurstChoice, NearDecision
    from media_hygiene.scan.models import BrokenFile, DuplicateGroup, MediaFile
    from media_hygiene.scan.sidecars import Sidecar


@dataclass(frozen=True, slots=True)
class KeepDecision:
    """One duplicate group: the copy that stays and the copies that go.

    `protected` copies lie in protected folders; `spared` ones were kept by a review
    decision (`clean --decisions`). Neither is ever removed.
    """

    digest: str
    size: int
    keeper: MediaFile
    removable: tuple[MediaFile, ...]
    protected: tuple[MediaFile, ...] = ()
    reason: KeepReason | None = None
    spared: tuple[MediaFile, ...] = ()

    @property
    def reclaimable(self) -> int:
        """Bytes freed by removing the removable copies.

        Returns:
            Size times the number of removable copies.
        """
        return self.size * len(self.removable)


@dataclass(frozen=True, slots=True)
class CleanPlan:
    """Everything `clean` would do, computed by `audit`."""

    decisions: tuple[KeepDecision, ...]
    broken: tuple[BrokenFile, ...]
    protected_broken: tuple[BrokenFile, ...] = ()
    near: tuple[NearDecision, ...] = ()
    sidecars: tuple[Sidecar, ...] = ()
    bursts: tuple[BurstChoice, ...] = ()
    delete_copies: bool = False  # `clean --delete`: exact copies deleted, not moved

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
            True when no duplicate copy, near duplicate, burst shot set aside,
            broken file or orphan sidecar is actionable.
        """
        return not (
            self.removable_count
            or self.broken
            or self.near_count
            or self.burst_count
            or self.orphans
        )

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
        return frozenset(exact | near | bursts | broken)


@dataclass(frozen=True, slots=True)
class AuditFindings:
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

    @property
    def files_scanned(self) -> int:
        """How many media files the audit analysed.

        Returns:
            The files of every folder.
        """
        return sum(self.folder_files.values())
