"""The clean use case: check the mounts, then execute the plan with a journal."""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.actions.clean import CleanExecutor
from media_hygiene.actions.journal import (
    JournalWriter,
    journal_file,
    latest_states,
    read_journal,
)
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.runs import new_run_id
from media_hygiene.constants import BrokenReason, Phase, Status
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import is_read_only
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.plan.models import AuditFindings, CleanPlan
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


class CleanService:
    """Refuses to act unless every action can be journaled and undone."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a clean.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def ensure_ready(self, *, near: bool = False, bursts: bool = False) -> None:
        """Check, before any analysis, that cleaning is possible and reversible.

        Args:
            near: Near duplicates will be moved to the quarantine (`--tier near`).
            bursts: Burst shots a review set aside will be moved there too.

        Raises:
            MountError: The journal is not persistent, a folder is read-only, the
                journal or the quarantine is not writable, or near duplicates, burst
                shots or copies of other files have no quarantine to go to.
        """
        runtime = self._runtime
        quarantine = runtime.persistent(MountKind.QUARANTINE)
        if near and not quarantine:
            raise MountError(
                _("--tier near moves near duplicates to /quarantine: mount it."),
                _('Add -v "<a folder of yours>:/quarantine" to handle them.'),
            )
        if bursts and not quarantine:
            raise MountError(
                _("Burst shots you set aside go to /quarantine: mount it."),
                _('Add -v "<a folder of yours>:/quarantine" to handle them.'),
            )
        if runtime.settings.scan.other_files and not quarantine:
            raise MountError(
                _("Copies of other files than media go to /quarantine: mount it."),
                _('Add -v "<a folder of yours>:/quarantine" to handle them.'),
            )
        if not runtime.persistent(MountKind.JOURNAL):
            raise MountError(
                _("No journal mount: without a journal, 'undo' would be impossible."),
                _('Add -v "<a folder of yours>:/journal" to the docker run command.'),
            )
        read_only = [
            root
            for root in runtime.mounts.data_roots(runtime.locations.data_dir)
            if root.is_dir() and is_read_only(root)
        ]
        if read_only:
            folders = ", ".join(runtime.mapper.to_host(root) for root in read_only)
            raise MountError(
                _("These folders are mounted read-only: {folders}.").format(
                    folders=folders
                ),
                _("Remove ':ro' from their -v options to let 'clean' act."),
            )
        ensure_writable(runtime, MountKind.JOURNAL, MountKind.QUARANTINE)

    def feasible(self, plan: CleanPlan) -> CleanPlan:
        """Drop what has to be moved when there is no quarantine to move it to.

        Unreadable files and orphan sidecars are moved, never deleted.

        Args:
            plan: The audited plan.

        Returns:
            The plan `clean` can execute safely.
        """
        if self._runtime.persistent(MountKind.QUARANTINE):
            return plan
        kept = tuple(item for item in plan.broken if item.reason is BrokenReason.EMPTY)
        if len(kept) != len(plan.broken) or plan.orphans:
            self._runtime.output.warning(
                _(
                    "No quarantine mount: unreadable files and orphan sidecars are "
                    "left in place."
                )
            )
            self._runtime.output.tip(
                _('Add -v "<a folder of yours>:/quarantine" to handle them.')
            )
        return replace(plan, broken=kept, sidecars=())

    def with_near(self, plan: CleanPlan, findings: AuditFindings) -> CleanPlan:
        """Add the near duplicates to the plan (`--tier near`).

        Args:
            plan: The feasible plan.
            findings: The audit, holding the near duplicates.

        Returns:
            The plan, near duplicates and the sidecars they leave orphan included.

        Near duplicates are moved to the quarantine, never deleted: `ensure_ready`
        with `near=True` has checked it is mounted.
        """
        return replace(plan, near=findings.similar.near)

    def execute(self, plan: CleanPlan) -> tuple[str, Outcome]:
        """Execute the plan under a new run identifier.

        Args:
            plan: What to clean.

        Returns:
            The run identifier and what was done.
        """
        locations = self._runtime.locations
        locations.journal_dir.mkdir(parents=True, exist_ok=True)
        run_id = new_run_id(locations.journal_dir)
        journal_path = journal_file(locations.journal_dir, run_id)
        with JournalWriter.open(journal_path) as journal:
            context = CleanContext(
                journal=journal,
                mapper=self._runtime.mapper,
                quarantine_run_dir=locations.quarantine_dir / run_id,
                progress=self._progress,
            )
            outcome = CleanExecutor(context).run(plan)
        self._forget_removed(journal_path)
        return run_id, outcome

    def _forget_removed(self, journal_path: Path) -> None:
        """Remove from the index the files this run deleted or moved away.

        `undo` needs nothing: the next audit indexes the restored files again.

        Args:
            journal_path: The journal of the run.
        """
        index = self._runtime.index_file
        if index is None:
            return
        latest = latest_states(read_journal(journal_path), Phase.CLEAN).values()
        removed = [entry.path for entry in latest if entry.status is Status.DONE]
        with FactsRepository.open(index) as repository:
            repository.forget(removed)
