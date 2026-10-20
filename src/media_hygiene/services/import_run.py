"""`media-hygiene import`: copy into the library what only a backup holds (0245).

The audit runs first, with the backup folders (`import_plan` decides the copies);
then each copy is journaled and proven (`actions.copy_in`): `undo` removes the
copies, the backup is never touched. Refused without a backup folder, without a
persistent journal, or on read-only photo folders, like every change of this tool.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.copy_in import CopyInExecutor
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.audit import AuditService
from media_hygiene.services.import_plan import plan_copies
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.policy import backup_folders

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.import_plan import ImportPlan
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class ImportResult:
    """What an `import` run did."""

    run_id: str
    outcome: Outcome
    interrupted: bool
    copied: tuple[Path, ...]  # the copies read back where they were written


class ImportService:
    """Audits with the backups, plans the copies, then copies: journaled, undoable."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a run.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def ensure_ready(self) -> None:
        """Check, before reading anything, that there is a backup and a safe place.

        Raises:
            MountError: No backup folder, no persistent journal, or the photo folders
                read-only.
        """
        if not backup_folders(self._runtime.settings, self._runtime.mapper).folders:
            raise MountError(
                _("No backup folder to import from."),
                _(
                    "Add one first: mh folders add --backup <folder>, or --backup "
                    "<folder> on this command."
                ),
            )
        ensure_can_act(self._runtime, Phase.IMPORT.value)

    def prepare(self, to: Path | None = None) -> ImportPlan:
        """Audit with the backups, then decide every copy.

        Args:
            to: The folder receiving the copies (container path); None: `From NAS`
                in the first photo folder.

        Returns:
            The plan.
        """
        findings = AuditService(self._runtime, self._progress).run()
        return plan_copies(self._runtime, findings.backups, to)

    def execute(self, plan: ImportPlan, stop: Callable[[], bool]) -> ImportResult:
        """Copy under a new run identifier.

        Args:
            plan: The copies.
            stop: Tells when Ctrl+C was pressed: the run stops between two files.

        Returns:
            The run, what it did, and the copies found where they were written.
        """
        tally = Tally()
        with new_run(self._runtime, self._progress, Phase.IMPORT) as context:
            interrupted = CopyInExecutor(context, tally).run(plan.jobs, stop)
        copied = tuple(job.target for job in plan.jobs if job.target.is_file())
        return ImportResult(
            context.quarantine_run_dir.name, tally.freeze(), interrupted, copied
        )
