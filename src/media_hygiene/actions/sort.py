"""Execute a sort: move each group of files into its folder, companions together.

Each file is checked again just before it moves (size and modification time, as
`classify` saw them): a changed or missing file is skipped, and so are its sidecars. A
stop asked for (Ctrl+C) is honoured between two groups, never in the middle of one.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.actions.outcome import Incident
from media_hygiene.actions.sort_moves import Relocator, file_of
from media_hygiene.actions.sort_names import free_names, owners, sidecars_of
from media_hygiene.actions.verify import change_blocker
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.outcome import Outcome, Tally
    from media_hygiene.actions.sort_moves import SortContext
    from media_hygiene.actions.sort_plan import Move, MoveGroup, SortPlan

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MoveOutcome:
    """What the moves did, the entries of the files moved, whether it stopped early."""

    outcome: Outcome
    moved: tuple[JournalEntry, ...]
    interrupted: bool


class SortExecutor:
    """Moves group by group; a problem on one file never stops the others."""

    def __init__(self, context: SortContext, tally: Tally) -> None:
        """Prepare a run.

        Args:
            context: Journal, plan and stop request.
            tally: Counters of the run, shared with the removal of emptied folders.
        """
        self._context = context
        self._tally = tally
        self.relocator = Relocator(context, tally)
        self._moved: list[JournalEntry] = []

    def run(self, plan: SortPlan) -> MoveOutcome:
        """Move every group of the plan, until done or asked to stop.

        Args:
            plan: The moves.

        Returns:
            What was moved, skipped, failed, and whether the run stopped early.
        """
        progress = self._context.changes.progress
        step = Step(
            _("Sorting"),
            _("Each file is checked again just before it moves; none is overwritten."),
        )
        progress.start(step, len(plan.moves))
        interrupted = False
        for group in plan.groups:
            if self._context.stop():
                interrupted = True
                break
            self._group(group)
        progress.stop()
        return MoveOutcome(self._tally.freeze(), tuple(self._moved), interrupted)

    def _group(self, group: MoveGroup) -> None:
        """Move the files of a group, then the sidecars of those that moved.

        Args:
            group: Files that travel together.
        """
        sidecars = sidecars_of(group)
        names = [move.source.name for move in group.moves]
        targets = free_names(group.folder, names + [path.name for path in sidecars])
        moved: set[str] = set()
        for move in group.moves:
            target = group.folder / targets[move.source.name]
            if self._guarded(move.source, partial(self._move, move, target)):
                moved.add(move.source.name)
            self._context.changes.progress.advance()
        for sidecar in sidecars:
            if all(name in moved for name in owners(sidecar.name, names)):
                target = group.folder / targets[sidecar.name]
                self._guarded(sidecar, partial(self._move_sidecar, sidecar, target))

    def _guarded(self, path: Path, action: Callable[[], bool]) -> bool:
        """Run one move, turning an OS error into a recorded failure.

        Args:
            path: File the move is about.
            action: The move; False when it was skipped.

        Returns:
            True when the file moved.
        """
        try:
            return action()
        except OSError as exc:
            _LOGGER.debug("Move failed on %s", path, exc_info=True)
            self._tally.failed.append(Incident(path, exc.strerror or str(exc)))
            return False

    def _move(self, move: Move, target: Path) -> bool:
        """Move one file of the plan, unless it changed since `classify`.

        Args:
            move: The file, as `classify` saw it.
            target: Where it goes.

        Returns:
            True when it moved.
        """
        file = file_of(move.source, (move.size, move.mtime_ns))
        blocker = change_blocker(file)
        if blocker is not None:
            self._tally.skipped.append(Incident(move.source, blocker))
            return False
        self._moved.append(self.relocator.move(file, target, move.row_id))
        return True

    def _move_sidecar(self, sidecar: Path, target: Path) -> bool:
        """Move a sidecar after the files it belongs to.

        Args:
            sidecar: The sidecar.
            target: Where it goes.

        Returns:
            True: it moved.
        """
        self._moved.append(self.relocator.move(file_of(sidecar), target))
        return True
