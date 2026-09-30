"""Reverse a run: rebuild deleted copies, unquarantine, move files and folders back."""

from __future__ import annotations

import logging
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, latest_states
from media_hygiene.actions.kinds import FOLDER_ACTIONS, Phase, Status
from media_hygiene.actions.outcome import Incident, Outcome, Tally
from media_hygiene.actions.restore import perform
from media_hygiene.actions.reversal import blocker, reversal_of
from media_hygiene.actions.runs import run_phase
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry, JournalWriter
    from media_hygiene.actions.reversal import Reversal
    from media_hygiene.scan.progress import ProgressSink

_LOGGER = logging.getLogger(__name__)


class UndoExecutor:
    """Reverses every action of a run not reversed yet, newest action first."""

    def __init__(self, journal: JournalWriter, progress: ProgressSink) -> None:
        """Prepare the undo of one run.

        Args:
            journal: The run's journal, opened for appending `undo` entries.
            progress: Where to report progress.
        """
        self._journal = journal
        self._progress = progress
        self._tally = Tally()

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
        restored = {entry.seq for entry in done_states(entries, Phase.UNDO)}
        todo = [
            (entry, reversal_of(entry))
            for seq, entry in sorted(latest_states(entries, run_phase(entries)).items())
            if seq not in restored
        ]
        step = Step(
            _("Restoring"),
            _(
                "Rebuilds each deleted copy from the kept one, brings quarantined and "
                "moved files back."
            ),
        )
        self._progress.start(step, len(todo))
        for entry, reversal in reversed(todo):
            try:
                self._restore(entry, reversal)
            except OSError as exc:
                _LOGGER.debug("Restore failed on %s", entry.path, exc_info=True)
                self._tally.failed.append(Incident(Path(entry.path), str(exc)))
            finally:
                self._progress.advance()
        self._progress.stop()
        return self._tally.freeze()

    def _restore(self, entry: JournalEntry, reversal: Reversal) -> None:
        """Reverse one action, journaling the undo like any other action.

        Args:
            entry: Latest state of the action to reverse.
            reversal: How it is reversed.
        """
        reason = blocker(entry, reversal)
        if reason is not None:
            self._tally.skipped.append(Incident(Path(entry.path), reason))
            return
        pending = entry.model_copy(
            update={"phase": Phase.UNDO, "status": Status.PENDING}
        )
        self._journal.record(pending)
        perform(entry, reversal)
        self._journal.record(pending.as_done())
        if entry.action in FOLDER_ACTIONS:  # a folder is not a file restored
            return
        self._tally.done += 1
        self._tally.bytes_done += entry.size
