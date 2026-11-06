"""The Undo of a page's toast: `mh undo <run>` of the run the page just made (0601).

A move to an event and *Apply now* write a journaled run; their toast's ↶ Undo asks the
page's server to reverse it. Only the latest run of the journal can be undone this way
(the one the page made, never an older one by mistake); each file is then looked for on
disk where it was, and the answer counts the files found back, not the ones meant to be.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.actions.undo import actions_to_undo
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.undo import runs_to_undo, undo_runs
from media_hygiene.services.undo_guard import ensure_undo_ready

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class UndoneRun:
    """A run reversed, as the disk holds it afterwards."""

    run_id: str
    meant: int  # the files the run had moved or set aside
    back: int  # of them, found again where they were
    failed: int  # refused or failed by the undo, said by it

    def said(self) -> dict[str, object]:
        """Return the answer the page shows.

        Returns:
            The run and its counts.
        """
        return {
            "run_id": self.run_id,
            "meant": self.meant,
            "back": self.back,
            "failed": self.failed,
            "intact": self.back == self.meant and not self.failed,
        }


@dataclass(frozen=True, slots=True)
class PageUndo:
    """Reverses the journal's latest run, for a page's Undo."""

    runtime: Runtime

    def latest(self) -> str | None:
        """Return the journal's latest run.

        Returns:
            Its id; None without a journal or a run.
        """
        if not self.runtime.persistent(MountKind.JOURNAL):
            return None
        runs = list_run_ids(self.runtime.locations.journal_dir)
        return runs[0] if runs else None

    def undo(self, run_id: str) -> UndoneRun:
        """Reverse a run, then look for its files where they were.

        Args:
            run_id: The run the page made; it must still be the latest.

        Returns:
            The counts read back from the disk.

        Raises:
            JournalError: The run is not the latest one any more (or unknown).
        """
        if run_id != self.latest():
            raise JournalError(
                _("Only the last run can be undone from this page: {run_id}.").format(
                    run_id=run_id
                ),
                _("Run 'media-hygiene undo {run_id}' in the terminal.").format(
                    run_id=run_id
                ),
            )
        plan = runs_to_undo(self.runtime, run_id)
        runs = [run_id] if plan is None else [each.run_id for each in plan.runs]
        ensure_undo_ready(self.runtime, runs)
        journal_dir = self.runtime.locations.journal_dir
        paths = [
            Path(entry.path)
            for run in runs
            for entry in actions_to_undo(read_journal(journal_file(journal_dir, run)))
            if entry.action is not ActionKind.CREATE_FOLDER  # undone: it is gone
        ]
        outcome = undo_runs(self.runtime, runs, NullProgress())
        back = sum(1 for path in paths if path.exists())  # a file, a folder removed
        return UndoneRun(run_id, len(paths), back, len(outcome.failed))
