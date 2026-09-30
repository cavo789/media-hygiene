"""The undo use case: pick a run, check the mounts, restore its files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import (
    JournalWriter,
    done_states,
    journal_file,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.actions.runs import list_run_ids, run_phase
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.errors import JournalError, MountError
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


def resolve_run_id(runtime: Runtime, run_id: str | None) -> str:
    """Return the requested run, or the latest one.

    Args:
        runtime: Settings, mount points and output.
        run_id: Explicit run identifier, or None for the latest.

    Returns:
        An existing run identifier.

    Raises:
        MountError: The journal is not mounted.
        JournalError: No run exists, or the requested one is unknown.
    """
    if not runtime.persistent(MountKind.JOURNAL):
        raise MountError(
            _("No journal mount: there is nothing to undo."),
            _('Mount the same journal folder as for clean: -v "<folder>:/journal".'),
        )
    runs = list_run_ids(runtime.locations.journal_dir)
    if not runs:
        raise JournalError(_("No run found in the journal."))
    if run_id is None:
        return runs[0]
    if run_id not in runs:
        raise JournalError(
            _("Unknown run {run_id}.").format(run_id=run_id),
            _("Run 'media-hygiene history' to list the runs."),
        )
    return run_id


def run_kind(runtime: Runtime, run_id: str) -> Phase:
    """Tell which command made a run.

    Args:
        runtime: Settings, mount points and output.
        run_id: An existing run.

    Returns:
        `clean` or `sort`.
    """
    return run_phase(read_journal(journal_file(runtime.locations.journal_dir, run_id)))


def undo_run(runtime: Runtime, run_id: str, progress: ProgressSink) -> Outcome:
    """Restore every file of a run.

    Args:
        runtime: Settings, mount points and output.
        run_id: Run to reverse.
        progress: Where to report progress.

    Returns:
        What was restored, skipped and why.
    """
    file = journal_file(runtime.locations.journal_dir, run_id)
    entries = read_journal(file)
    with JournalWriter.open(file) as journal:
        outcome = UndoExecutor(journal, progress).run(entries)
    _follow_moves_back(runtime, file)
    return outcome


def _follow_moves_back(runtime: Runtime, file: Path) -> None:
    """Update the index: files moved back by `undo` keep their facts.

    Args:
        runtime: Settings, mount points and output.
        file: The journal of the run.
    """
    index = runtime.index_file
    back = [
        (entry.target, entry.path)
        for entry in done_states(read_journal(file), Phase.UNDO)
        if entry.action is ActionKind.MOVE and entry.target
    ]
    if index is None or not back:
        return
    with FactsRepository.open(index) as repository:
        repository.move(back)
