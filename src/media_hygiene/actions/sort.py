"""Execute a sort: move each group of files into its folder, companions together.

Each file is checked again just before it moves (as `classify` saw it): a changed or
missing file is skipped, and so are its sidecars. A few groups move at once (0163),
their names decided first, in order, in the calling thread. Ctrl+C is
honoured between two groups: those under way end, no other one starts.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.actions.outcome import Incident, why
from media_hygiene.actions.parallel import Runner, run_all, stopping_on
from media_hygiene.actions.sort_groups import Ledger, NameBook
from media_hygiene.actions.sort_moves import Relocator, file_of
from media_hygiene.actions.sort_names import owners
from media_hygiene.actions.verify import change_blocker
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable, Iterator
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.outcome import Outcome, Tally
    from media_hygiene.actions.sort_groups import ReadyGroup
    from media_hygiene.actions.sort_moves import SortContext
    from media_hygiene.actions.sort_plan import Move, SortPlan

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class MoveOutcome:
    """What the moves did, the entries of the files moved, whether it stopped early."""

    outcome: Outcome
    moved: tuple[JournalEntry, ...]  # in the order they were journaled
    interrupted: bool


class SortExecutor:
    """Moves a few groups at a time; a problem on one file never stops the others."""

    def __init__(self, context: SortContext, tally: Tally) -> None:
        """Prepare a run.

        Args:
            context: Journal, plan and stop request.
            tally: Counters of the run, shared with the removal of emptied folders.
        """
        self._context = context
        self._tally = tally
        self.relocator = Relocator(context, tally)
        self._ledger = Ledger()
        self._names = NameBook()
        self._interrupted = False

    def run(self, plan: SortPlan) -> MoveOutcome:
        """Move every group of the plan, until done or asked to stop.

        Args:
            plan: The moves.

        Returns:
            What was moved, skipped, failed, and whether the run stopped early.
        """
        changes = self._context.changes
        step = Step(
            _("Sorting"),
            _("Each file is checked again just before it moves; none is overwritten."),
        )
        changes.progress.start(step, len(plan.moves))
        runner = Runner(
            self._group,
            self._shown,
            changes.workers,
            stopping=stopping_on(changes.progress),
        )
        run_all(self._ready(plan), runner)
        changes.progress.stop()
        moved = self._ledger.entries()
        return MoveOutcome(self._tally.freeze(), moved, self._interrupted)

    def _ready(self, plan: SortPlan) -> Iterator[ReadyGroup]:
        """Give each group its names, in order, until asked to stop.

        Args:
            plan: The moves.

        Yields:
            The groups, ready to move (calling thread: names given in order).
        """
        for group in plan.groups:
            if self._context.stop():
                self._interrupted = True
                return
            yield self._names.ready(group)

    def _group(self, ready: ReadyGroup) -> None:
        """Move the files of a group, then the sidecars of those that moved (worker).

        Args:
            ready: Files that travel together, and their names.
        """
        group, names = ready.group, ready.names
        moved: set[str] = set()
        for move in group.moves:
            target = group.folder / ready.targets[move.source.name]
            if self._guarded(move.source, partial(self._move, move, target)):
                moved.add(move.source.name)
        for sidecar in ready.sidecars:
            if all(name in moved for name in owners(sidecar.name, names)):
                target = group.folder / ready.targets[sidecar.name]
                self._guarded(sidecar, partial(self._move_sidecar, sidecar, target))

    def _shown(self, ready: ReadyGroup) -> None:
        """Advance the bar by a group's files, hand its names back (calling thread).

        Args:
            ready: A group that ended.
        """
        self._names.release(ready)
        for _move in ready.group.moves:
            self._context.changes.progress.advance()

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
            self._ledger.add(self._tally.failed, Incident(path, why(exc)))
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
            self._ledger.add(self._tally.skipped, Incident(move.source, blocker))
            return False
        self._ledger.moved(self.relocator.move(file, target, move.row_id))
        return True

    def _move_sidecar(self, sidecar: Path, target: Path) -> bool:
        """Move a sidecar after the files it belongs to.

        Args:
            sidecar: The sidecar.
            target: Where it goes.

        Returns:
            True: it moved.
        """
        self._ledger.moved(self.relocator.move(file_of(sidecar), target))
        return True
