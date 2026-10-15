"""Reverse a run: rebuild deleted copies, unquarantine, move files and folders back.

A few files come back at once, as `clean` set them aside (0161, `undo_chains`).
"""

from __future__ import annotations

import logging
import threading
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import done_states, latest_states
from media_hygiene.actions.kinds import FOLDER_ACTIONS, ActionKind, Phase, Status
from media_hygiene.actions.outcome import Incident, Outcome, Tally, why
from media_hygiene.actions.parallel import WORKERS, Runner, run_all, stopping_on
from media_hygiene.actions.quarantine import LeftFolders
from media_hygiene.actions.restore import perform
from media_hygiene.actions.reversal import (
    XMP_REVERSALS,
    Reversal,
    blocker,
    reversal_of,
)
from media_hygiene.actions.runs import run_phase
from media_hygiene.actions.undo_chains import stages
from media_hygiene.actions.xmp_undo import never_written
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry, JournalWriter
    from media_hygiene.actions.undo_chains import Chain
    from media_hygiene.scan.progress import ProgressSink

_LOGGER = logging.getLogger(__name__)
# Undone by removing what the action created: the path existing proves it happened.
_NOT_ABOUT_THE_PATH: Final = frozenset(
    {Reversal.REMOVE_CREATED_FOLDER, Reversal.REMOVE_LINK, Reversal.REMOVE_MARKER}
)


def actions_to_undo(entries: list[JournalEntry]) -> list[JournalEntry]:
    """List the actions of a run not reversed yet, in sequence order.

    Args:
        entries: Every entry of the run's journal.

    Returns:
        The latest state of each action no `undo` has reversed.
    """
    restored = {entry.seq for entry in done_states(entries, Phase.UNDO)}
    latest = latest_states(entries, run_phase(entries))
    return [latest[seq] for seq in sorted(latest) if seq not in restored]


class UndoExecutor:
    """Reverses every action of a run not reversed yet, newest first, a few at once."""

    def __init__(
        self, journal: JournalWriter, progress: ProgressSink, workers: int = WORKERS
    ) -> None:
        """Prepare the undo of one run.

        Args:
            journal: The run's journal, opened for appending `undo` entries.
            progress: Where to report progress.
            workers: How many files are put back at once (`[clean] workers`).
        """
        self._journal = journal
        self._workers = workers
        self._progress = progress
        self._tally = Tally()
        self._lock = threading.Lock()  # the tally, filled by several workers
        self._left = LeftFolders()
        self._restoring = _("Putting back: {path}")

    def run(self, entries: list[JournalEntry]) -> Outcome:
        """Reverse the actions of the run, `clean` or `sort`.

        Every action is checked to be reversible before the first file is touched.

        Args:
            entries: Every entry of the run's journal.

        Returns:
            What was restored, skipped and why.

        Raises:
            JournalError: An action cannot be undone by this version (raised before
                anything changes).
        """
        todo = [(entry, reversal_of(entry)) for entry in actions_to_undo(entries)]
        step = Step(
            _("Restoring"),
            _(
                "Rebuilds each deleted copy from the kept one, brings quarantined and "
                "moved files back."
            ),
            total_weight=sum(entry.size for entry, _reversal in todo),
        )
        self._progress.start(step, len(todo))
        runner = Runner(
            self._reverse,
            self._shown,
            self._workers,
            stopping=stopping_on(self._progress),
        )
        try:
            for stage in stages(todo[::-1]):
                run_all(stage, runner if len(stage) > 1 else replace(runner, workers=1))
        finally:  # an undo stopped halfway still removes the folders it emptied
            self._left.remove()
        self._progress.stop()
        return self._tally.freeze()

    def _reverse(self, chain: Chain) -> None:
        """Reverse a chain of actions, in its order (a worker thread).

        Args:
            chain: Actions sharing a path, newest first.
        """
        for entry, reversal in chain:
            try:
                self._restore(entry, reversal)
            except OSError as exc:
                _LOGGER.debug("Restore failed on %s", entry.path, exc_info=True)
                with self._lock:
                    self._tally.failed.append(Incident(Path(entry.path), why(exc)))

    def _shown(self, chain: Chain) -> None:
        """Say which files came back, and advance the bar (the calling thread).

        Args:
            chain: The actions just reversed.
        """
        for entry, _reversal in chain:
            self._progress.current(self._restoring.format(path=entry.host_path))
            self._progress.advance(entry.size)

    def _restore(self, entry: JournalEntry, reversal: Reversal) -> None:
        """Reverse one action, journaling the undo like any other action.

        Args:
            entry: Latest state of the action to reverse.
            reversal: How it is reversed.
        """
        if _never_happened(entry, reversal):
            _LOGGER.debug("Interrupted before acting, nothing to undo: %s", entry.path)
            return
        reason = blocker(entry, reversal)
        if reason is not None:
            with self._lock:
                self._tally.skipped.append(Incident(Path(entry.path), reason))
            return
        pending = entry.model_copy(
            update={"phase": Phase.UNDO, "status": Status.PENDING}
        )
        self._journal.record(pending)
        perform(entry, reversal)
        self._journal.record(pending.as_done())
        if reversal is Reversal.UNQUARANTINE and entry.quarantine:
            self._left.note(Path(entry.path), Path(entry.quarantine))
        if entry.action in FOLDER_ACTIONS:  # a folder is not a file restored
            return
        with self._lock:
            self._tally.done += 1
            if entry.action is not ActionKind.LINK:  # removing a link frees nothing
                self._tally.bytes_done += entry.size


def _never_happened(entry: JournalEntry, reversal: Reversal) -> bool:
    """Tell whether a run stopped before this action changed anything.

    A `pending` action may have happened (stopped before its `done` line) or not
    (stopped before it acted). A file still where the action would have taken it
    from was never touched: there is nothing to undo, and nothing to warn about.

    Args:
        entry: Latest state of the action.
        reversal: How it is undone.

    Returns:
        True for a `pending` file action whose file is still in place.
    """
    if reversal in XMP_REVERSALS:
        return never_written(entry)
    return (
        entry.status is Status.PENDING
        and reversal not in _NOT_ABOUT_THE_PATH
        and Path(entry.path).exists()
    )
