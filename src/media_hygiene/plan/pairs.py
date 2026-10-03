"""Folder pairs: which folder keeps its copies, which one loses them, and the gain."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.constants import MediaKind

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.constants import KeepReason
    from media_hygiene.plan.models import KeepDecision
    from media_hygiene.scan.models import MediaFile


class Disposal(StrEnum):
    """What `clean` does with the copies of a folder pair.

    Every copy is moved to the quarantine; with `clean --delete`, media copies are
    deleted and copies of other files (`--ext pdf`) moved. A pair can hold both.
    """

    DELETED = "deleted"
    MOVED = "moved"
    MIXED = "mixed"


@dataclass(frozen=True, slots=True)
class Copy:
    """One copy to delete, and the identical file that stays."""

    kept: MediaFile
    removed: MediaFile
    digest: str
    size: int
    reason: KeepReason | None = None
    delete_copies: bool = False  # `clean --delete`

    @property
    def moved(self) -> bool:
        """Tell whether `clean` moves this copy to the quarantine rather than delete it.

        Returns:
            True by default; with `--delete`, for another file than a media only.
        """
        return self.removed.kind is MediaKind.OTHER or not self.delete_copies


@dataclass(frozen=True, slots=True)
class FolderPair:
    """Two folders sharing identical files: the fastest way to sanity-check a clean.

    `complete` means every analysed media file of `removed_from` goes, each with a copy
    kept in `kept_in`: the folder is entirely a copy of the other one.
    """

    kept_in: Path
    removed_from: Path
    copies: tuple[Copy, ...]
    complete: bool = False

    @property
    def files(self) -> int:
        """Number of copies deleted from `removed_from`.

        Returns:
            The count.
        """
        return len(self.copies)

    @property
    def size(self) -> int:
        """Bytes freed by deleting them.

        Returns:
            The byte count.
        """
        return sum(copy.size for copy in self.copies)

    @property
    def disposal(self) -> Disposal:
        """Whether the copies are deleted, moved to the quarantine, or both.

        Returns:
            The disposal of the pair.
        """
        moved = sum(copy.moved for copy in self.copies)
        if not moved:
            return Disposal.DELETED
        return Disposal.MOVED if moved == len(self.copies) else Disposal.MIXED


def folder_pairs(
    decisions: Iterable[KeepDecision],
    folder_files: Mapping[Path, int] | None = None,
    *,
    delete_copies: bool = False,
) -> tuple[FolderPair, ...]:
    """Group the copies to remove by (kept folder, folder losing the copy).

    Args:
        decisions: The keep decisions of a plan.
        folder_files: Media files analysed per folder, to tell complete copies.
        delete_copies: `clean --delete`: media copies are deleted, not moved.

    Returns:
        The pairs, the most space freed first (then the most files, then by path).
    """
    grouped: defaultdict[tuple[Path, Path], list[Copy]] = defaultdict(list)
    for decision in decisions:
        for file in decision.removable:
            key = (decision.keeper.path.parent, file.path.parent)
            grouped[key].append(
                Copy(
                    decision.keeper,
                    file,
                    decision.digest,
                    decision.size,
                    decision.reason,
                    delete_copies,
                )
            )
    counts = folder_files or {}
    pairs = (
        FolderPair(
            kept_in,
            removed_from,
            tuple(copies),
            complete=kept_in != removed_from
            and counts.get(removed_from) == len(copies),
        )
        for (kept_in, removed_from), copies in grouped.items()
    )
    return tuple(
        sorted(
            pairs,
            key=lambda pair: (
                -pair.size,
                -pair.files,
                str(pair.kept_in),
                str(pair.removed_from),
            ),
        )
    )
