"""A run of *Try on one month* as the page shows it, and read back from the journal."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.sort_resume import OpenTrial


@dataclass(frozen=True, slots=True)
class TrialRun:
    """A run of the page, read back from its journal entries."""

    run_id: str
    moved: int
    verified: int
    intact: bool
    targets: tuple[Path, ...]  # where the files went, by folder
    rest: int  # files still to move afterwards


def read_back(trial: OpenTrial, rest: int) -> TrialRun:
    """The trial still open as it stands on the disk (0648).

    A file moved since in Explorer is no longer at its target: no tile, the run not
    intact; `undo` says the same when it looks for it.

    Args:
        trial: What the journal holds.
        rest: The files still to move.

    Returns:
        The run.
    """
    there = tuple(sorted(_found(trial.moves)))
    moved = len(trial.moves)
    return TrialRun(
        trial.run_id,
        moved,
        len(there),
        intact=len(there) == moved,
        targets=there,
        rest=rest,
    )


def _found(moves: tuple[JournalEntry, ...]) -> Iterator[Path]:
    """The moved files still at their new place.

    Args:
        moves: The journal's moves.

    Yields:
        Each target holding a file of the size journaled.
    """
    for move in moves:
        target = Path(move.target or move.path)
        if target.is_file() and target.stat().st_size == move.size:
            yield target
