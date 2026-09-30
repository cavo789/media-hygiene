"""What `sort` will do: groups of files, each moving into one folder, and what stays."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.models import Band

if TYPE_CHECKING:
    from pathlib import Path

_TO_SORT: Final = frozenset({Band.MANUAL, Band.UNDATED})


@dataclass(frozen=True, slots=True)
class Move:
    """One file of the plan, as `classify` saw it."""

    row_id: str
    source: Path  # container path
    size: int
    mtime_ns: int
    band: Band  # once the edits are applied


@dataclass(frozen=True, slots=True)
class MoveGroup:
    """Files that travel together into one folder, the leading one first."""

    root: Path  # the target root the folder is relative to (container path)
    folder: Path  # container path
    moves: tuple[Move, ...]


@dataclass(frozen=True, slots=True)
class SortPlan:
    """The moves of one run, and what stays."""

    plan_id: str
    groups: tuple[MoveGroup, ...]
    in_place: int = 0  # already in their folder: counted, not moved
    stay: int = 0  # stay where they are: edits, protected and `leave` folders
    done: int = 0  # moved by an earlier run of this plan
    moved_before: tuple[Path, ...] = ()  # where those were: their folders may be empty

    @property
    def moves(self) -> tuple[Move, ...]:
        """Every file to move.

        Returns:
            Them, group by group.
        """
        return tuple(move for group in self.groups for move in group.moves)

    @property
    def size(self) -> int:
        """The bytes to move.

        Returns:
            Their sum.
        """
        return sum(move.size for move in self.moves)

    @property
    def folders(self) -> frozenset[Path]:
        """The folders receiving files.

        Returns:
            Them.
        """
        return frozenset(group.folder for group in self.groups)

    @property
    def roots(self) -> frozenset[Path]:
        """The target roots of the moves.

        Returns:
            Them.
        """
        return frozenset(group.root for group in self.groups)

    def count(self, bands: frozenset[Band]) -> int:
        """Count the files to move in some bands.

        Args:
            bands: The bands.

        Returns:
            How many files to move are in them.
        """
        return sum(1 for move in self.moves if move.band in bands)

    @property
    def to_sort(self) -> int:
        """The files going to a "to sort" folder.

        Returns:
            Their count.
        """
        return self.count(_TO_SORT)
