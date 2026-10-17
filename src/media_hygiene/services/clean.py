"""The clean use case: check the mounts, then execute the plan with a journal."""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.clean import CleanExecutor
from media_hygiene.actions.journal import (
    JournalWriter,
    done_states,
    journal_file,
    read_journal,
)
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.runs import new_run_id
from media_hygiene.constants import BrokenReason
from media_hygiene.i18n import _
from media_hygiene.index.parked import park
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.missing_mount import missing_mount, typed_again
from media_hygiene.services.next_command import CHANGING, NextVerb
from media_hygiene.services.quarantine_space import quarantine_route

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class CleanMode:
    """What a clean will do, as its options ask."""

    near: bool = False  # `--tier near`: near duplicates go to the quarantine too
    bursts: bool = False  # `--decisions`: burst shots, files chosen go there too
    delete: bool = False  # `--delete`: exact copies deleted for good, not moved


# The default clean: exact copies to the quarantine.
EXACT: Final = CleanMode()


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

    def ensure_ready(self, mode: CleanMode = EXACT) -> None:
        """Check, before any analysis, that cleaning is possible and reversible.

        Args:
            mode: What the clean will do.

        Raises:
            MountError: The journal is not persistent, a folder is read-only, the
                journal or the quarantine is not writable, or what goes to the
                quarantine (exact copies unless `--delete`, near duplicates, burst
                shots, copies of other files) has no quarantine to go to.
        """
        runtime = self._runtime
        if not runtime.persistent(MountKind.QUARANTINE):
            message = _quarantine_needed(runtime, mode)
            if message is not None:
                again = NextVerb(typed_again(runtime, "clean"), CHANGING)
                raise missing_mount(runtime, message, again)
        ensure_can_act(runtime, "clean")

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
                delete_copies=plan.delete_copies,
                workers=self._runtime.settings.clean.workers,
                route=quarantine_route(self._runtime),
            )
            outcome = CleanExecutor(context).run(plan)
        self._forget_removed(journal_path, run_id)
        return run_id, outcome

    def _forget_removed(self, journal_path: Path, run_id: str) -> None:
        """Take out of the index the files this run deleted or moved away.

        The rows of a file set aside are parked (`index.parked`): `undo` puts them
        back, `purge` drops them. Those of a file deleted are forgotten.

        Args:
            journal_path: The journal of the run.
            run_id: The run.
        """
        index = self._runtime.index_file
        if index is None:
            return
        done = done_states(read_journal(journal_path), Phase.CLEAN)
        aside = [(entry.path, entry.quarantine) for entry in done if entry.quarantine]
        deleted = [entry.path for entry in done if not entry.quarantine]
        with FactsRepository.open(index) as repository:
            park(repository.connection, run_id, aside)
            repository.forget(deleted)


def _quarantine_needed(runtime: Runtime, mode: CleanMode) -> str | None:
    """Say why this clean needs a quarantine, if it does.

    Args:
        runtime: Settings, mount points and output.
        mode: What the clean will do.

    Returns:
        The translated reason, or None when nothing goes to the quarantine.
    """
    if not mode.delete:
        return _("clean moves the duplicate copies to /quarantine: mount it.")
    if mode.near:
        return _("--tier near moves near duplicates to /quarantine: mount it.")
    if mode.bursts:
        return _("The burst shots and files you set aside go to /quarantine: mount it.")
    if runtime.settings.scan.other_files:
        return _("Copies of other files than media go to /quarantine: mount it.")
    return None
