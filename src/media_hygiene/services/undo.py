"""The undo use case: pick a run, check the mounts, restore its files."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import (
    JournalWriter,
    journal_file,
    read_journal,
)
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import combine
from media_hygiene.actions.plan_runs import runs_of_plan
from media_hygiene.actions.runs import list_run_ids, run_phase
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.actions.undo_pick import RunPick, picked_entries
from media_hygiene.console.links_view import show_links
from media_hygiene.errors import JournalError, MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.drive_letter import found_line, relocate, tidy
from media_hygiene.services.journal_beside import copy_beside, take_back_journals
from media_hygiene.services.quarantines import letter_changes
from media_hygiene.services.shrink_links import renamed
from media_hygiene.services.sort_links import follow_links
from media_hygiene.services.undo_index import follow_moves_back

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.actions.plan_runs import PlanRuns
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
    take_back_journals(runtime)  # `/journal` wiped: the copies beside the quarantine
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


def runs_to_undo(runtime: Runtime, run_id: str) -> PlanRuns | None:
    """Tell which runs `undo <run>` reverses.

    A `sort` stopped then resumed is one operation for the user: every run of its plan
    not undone yet goes, newest first. A `clean` run goes alone.

    Args:
        runtime: Settings, mount points and output.
        run_id: The run named (or the latest one).

    Returns:
        The runs of the sort to undo, newest first; None for a `clean` run.
    """
    if run_kind(runtime, run_id) is not Phase.SORT:
        return None
    return runs_of_plan(runtime.locations.journal_dir, run_id)


def undo_runs(
    runtime: Runtime, run_ids: Sequence[str], progress: ProgressSink
) -> Outcome:
    """Restore the files of several runs, in the order given (newest first).

    Each run's journal records its own `undo` entries, and the index follows each.

    Args:
        runtime: Settings, mount points and output.
        run_ids: The runs, newest first.
        progress: Where to report progress.

    Returns:
        What was restored, skipped and why, summed over the runs.
    """
    return combine([undo_run(runtime, run_id, progress) for run_id in run_ids])


def undo_run(runtime: Runtime, run_id: str, progress: ProgressSink) -> Outcome:
    """Restore every file of a run, under the new letter of a drive that changed.

    Args:
        runtime: Settings, mount points and output.
        run_id: Run to reverse.
        progress: Where to report progress.

    Returns:
        What was restored, skipped and why.
    """
    return undo_pick(runtime, RunPick(run_id), progress)


def undo_pick(runtime: Runtime, pick: RunPick, progress: ProgressSink) -> Outcome:
    """Restore the files picked of a run (every one without a pick), journaled.

    Args:
        runtime: Settings, mount points and output.
        pick: The run, and the actions to reverse (0525: a few quarantined files).
        progress: Where to report progress.

    Returns:
        What was restored, skipped and why.
    """
    run_id = pick.run_id
    file = journal_file(runtime.locations.journal_dir, run_id)
    changes = letter_changes(runtime, run_id)
    for change in changes:
        runtime.output.info(found_line(change, run_id))
    entries, refused = relocate(read_journal(file), changes)
    with JournalWriter.open(file) as journal:
        executor = UndoExecutor(journal, progress, runtime.settings.clean.workers)
        outcome = executor.run(picked_entries(entries, pick.seqs))
    for change in changes:
        tidy(change, run_id)
    copy_beside(runtime, run_id)  # what is left aside; none once all came back (0697)
    back = follow_moves_back(runtime, (file, run_id), changes)
    back += renamed(file, Phase.UNDO)  # a video `shrink` renamed (0418)
    show_links(runtime.output, follow_links(runtime, back))
    return replace(outcome, skipped=(*outcome.skipped, *refused))
