"""What `mh backup` does to its target: only what it lacks, a move as a rename (0264).

Pure: the files of the sources and of the target, each by its path relative to the
target (`C/Photos/2024/IMG_1.jpg`), with its size and modification time. A path is
compared without case, as Windows and the NAS compare it. Same path, size and time
(within robocopy's two seconds, `/FFT`): nothing to do. A path of the target the PC no
longer has, of the same size and time as a new path of the PC and the same content
(`Same`, the first and last 64 KiB): a move on the target, nothing sent again; ties
between identical copies broken by name. The same path with another size or time: the
target's copy set aside first, then copied again, but never by a file the audit found
broken. A target file the PC no longer has at all: gone, with the reason the tool knows.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.plan.backup_entries import (
    Edit,
    Entry,
    Move,
    Stat,
)
from media_hygiene.plan.backup_gone import Gone, GoneReason

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping

# Compares the content of a new PC file and a target file (partial digests).
type Same = Callable[[str, str], bool]


@dataclass(frozen=True, slots=True)
class BackupInputs:
    """The files on each side, and what the tool knows of the PC's."""

    source: Mapping[str, Stat]
    target: Mapping[str, Stat]
    broken: frozenset[str] = frozenset()  # PC files the audit found broken
    reasons: Mapping[str, GoneReason] | None = None  # target path → why gone


@dataclass(frozen=True, slots=True)
class BackupPlan:
    """What the target needs: moves, copies, set-asides; and what is left alone."""

    held: int  # files of the target, below the sources taking part
    unchanged: int = 0
    new: tuple[Entry, ...] = ()
    edited: tuple[Edit, ...] = ()
    moves: tuple[Move, ...] = ()
    broken: tuple[Entry, ...] = ()  # PC files kept from replacing their copy
    gone: tuple[Gone, ...] = ()

    @property
    def removals(self) -> tuple[Gone, ...]:
        """The files gone that are proposed for removal: purged or confirmed.

        Returns:
            Them, in path order.
        """
        return tuple(gone for gone in self.gone if gone.reason.proposed)

    @property
    def kept(self) -> tuple[Gone, ...]:
        """The files gone that stay in the backup, their reason counted.

        Returns:
            Them, in path order.
        """
        return tuple(gone for gone in self.gone if not gone.reason.proposed)

    @property
    def copies(self) -> tuple[Entry, ...]:
        """Every file robocopy is to copy: the new ones, then the edited ones.

        Returns:
            Them, by the PC's path.
        """
        return (*self.new, *(edit.new for edit in self.edited))

    def stops(self, percent: int) -> bool:
        """Tell whether the set-asides and replacements exceed a share of the backup.

        Args:
            percent: `[backup] stop_above_percent`.

        Returns:
            True when more than that share would be set aside or replaced.
        """
        touched = len(self.removals) + len(self.edited)
        return self.held > 0 and touched * 100 > percent * self.held


def plan_backup(inputs: BackupInputs, same: Same) -> BackupPlan:
    """Compare the sources with the target.

    Args:
        inputs: The files of both sides, the broken ones, the reasons.
        same: Compares the content of a new PC file and a target file.

    Returns:
        The plan.
    """
    target = {path.casefold(): path for path in inputs.target}
    unchanged = 0
    new: list[Entry] = []
    edited: list[Edit] = []
    broken: list[Entry] = []
    for path in sorted(inputs.source):
        stat = inputs.source[path]
        old = target.pop(path.casefold(), None)
        if old is None:
            new.append(Entry(path, stat))
        elif inputs.target[old].same(stat):
            unchanged += 1
        elif path in inputs.broken:
            broken.append(Entry(path, stat))
        else:
            edited.append(Edit(Entry(old, inputs.target[old]), Entry(path, stat)))
    orphans = [Entry(path, inputs.target[path]) for path in sorted(target.values())]
    moves = _moves(orphans, new, same)
    arrived = {move.new for move in moves}
    left = {move.old.path for move in moves}
    reasons = inputs.reasons or {}
    return BackupPlan(
        held=len(inputs.target),
        unchanged=unchanged,
        new=tuple(entry for entry in new if entry.path not in arrived),
        edited=tuple(edited),
        moves=moves,
        broken=tuple(broken),
        gone=tuple(
            Gone(entry, reasons.get(entry.path, GoneReason.UNKNOWN))
            for entry in orphans
            if entry.path not in left
        ),
    )


def _moves(orphans: list[Entry], new: list[Entry], same: Same) -> tuple[Move, ...]:
    """Pair each orphan of the target with a new PC file holding its content.

    Args:
        orphans: The target files the PC no longer has at their path, by name.
        new: The PC files the target lacks at their path, by name.
        same: Compares their content.

    Returns:
        The moves: each orphan with the first new file, by name, of the same size,
        time and content not taken yet.
    """
    by_size: dict[int, list[Entry]] = {}
    for entry in new:
        by_size.setdefault(entry.stat.size, []).append(entry)
    taken: set[str] = set()
    moves: list[Move] = []
    for orphan in orphans:
        for candidate in by_size.get(orphan.stat.size, ()):
            if candidate.path in taken or not candidate.stat.same(orphan.stat):
                continue
            if same(candidate.path, orphan.path):
                taken.add(candidate.path)
                moves.append(Move(orphan, candidate.path))
                break
    return tuple(moves)
