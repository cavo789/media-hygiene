"""Restore a damaged file from its good copy: journaled, proven, undoable (0690).

The good copy is copied under a temporary name beside the damaged file and read back;
only then the damaged file goes to the quarantine (journaled `quarantine`, its SHA-256
as read) and the copy takes its name and its time (journaled `copy-in`, `keeper` the
good copy). `undo` removes the copy while it holds the good bytes, then brings the
damaged file back. Never over a file: the name must be free when the copy takes it.
"""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.job_loop import JobLoop
from media_hygiene.actions.journaled import JournaledChanges, Origin
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.no_overwrite import copy_exclusive, rename_no_replace
from media_hygiene.actions.sort_moves import file_of
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally

_TEMPORARY: Final = ".media-hygiene.tmp"


@dataclass(frozen=True, slots=True)
class RepairJob:
    """One file to restore: its place, the version found damaged, the good copy."""

    target: Path
    stat: tuple[int, int]  # size and time of the damaged version
    copy: Path
    digest: str  # the good SHA-256


class RepairExecutor:
    """Journals and makes the restorations of one run."""

    def __init__(self, context: CleanContext, tally: Tally) -> None:
        """Prepare a run.

        Args:
            context: Where to journal, set aside and report progress.
            tally: Counters: one per file restored.
        """
        self._changes = JournaledChanges(context, tally)
        self._context = context
        self._tally = tally
        self.restored: list[Path] = []

    def run(self, jobs: Sequence[RepairJob], stop: Callable[[], bool]) -> bool:
        """Restore every file; one that fails is counted, the others go on.

        Args:
            jobs: The files.
            stop: Tells when Ctrl+C was pressed.

        Returns:
            True when Ctrl+C stopped the run.
        """
        step = Step(
            _("Restoring"),
            _("Copies the good copy, checks it, then sets the damaged file aside."),
        )
        loop = JobLoop(self._context.progress, step, self._tally, self._one, _target)
        return loop.run(jobs, stop)

    def _one(self, job: RepairJob) -> None:
        """Copy and prove, set the damaged file aside, give the copy its name.

        Args:
            job: The file.

        Raises:
            ValueError: It changed since it was found damaged.
            OSError: The copy does not hold the good content.
        """
        damaged = file_of(job.target)
        if (damaged.size, damaged.mtime_ns) != job.stat:
            raise ValueError(_("it changed since it was found damaged: kept"))
        temporary = job.target.with_name(job.target.name + _TEMPORARY)
        try:
            _prove(job, copy_exclusive(job.copy, temporary), temporary)
            os.utime(temporary, ns=(damaged.mtime_ns, damaged.mtime_ns))
            self._changes.quarantine(damaged, ActionKind.QUARANTINE, Origin(job.copy))
        except OSError:
            with contextlib.suppress(OSError):
                temporary.unlink()
            raise
        entry = self._changes.entry(damaged, ActionKind.COPY_IN)
        entry = entry.model_copy(update={"keeper": str(job.copy)})
        journal = self._context.journal
        journal.record(entry)
        rename_no_replace(temporary, job.target)
        journal.record(entry.as_done().model_copy(update={"sha256": job.digest}))
        self._changes.count(damaged.size)
        self.restored.append(job.target)


def _prove(job: RepairJob, read: str, temporary: Path) -> None:
    """The good copy read as it was copied, then the copy read back.

    Args:
        job: The restoration.
        read: The SHA-256 of the good copy, as read while copying.
        temporary: The copy.

    Raises:
        OSError: One of them does not hold the good content.
    """
    if read != job.digest:
        raise OSError(_("the good copy changed: nothing restored"))
    if full_digest(temporary) != job.digest:
        raise OSError(_("the copy does not match its source"))


def _target(job: RepairJob) -> Path:
    """The file a failure is told about.

    Args:
        job: The restoration.

    Returns:
        The damaged file.
    """
    return job.target
