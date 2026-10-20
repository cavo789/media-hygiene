"""Copy into the library what only a backup holds: journaled, proven, never over a file.

Each copy is journaled `pending` first, written under a temporary name next to its
place (the source hashed as it is read: a NAS is read once), read back and hashed,
then renamed to its name only if that name is still free. Its journal entry is
marked `done` with the SHA-256: `undo` removes the copy while it holds those bytes.
The backup is only read.
"""

from __future__ import annotations

import contextlib
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journaled import JournaledChanges
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.no_overwrite import copy_exclusive, rename_no_replace
from media_hygiene.actions.outcome import Incident, why
from media_hygiene.actions.sort_moves import file_of, make_folders, target_exists
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally

_LOGGER = logging.getLogger(__name__)
_TEMPORARY: Final = ".media-hygiene.tmp"


@dataclass(frozen=True, slots=True)
class CopyJob:
    """One file to copy: from the backup (`source`) to its place in the library."""

    source: Path
    target: Path


class CopyInExecutor:
    """Journals and makes the copies of one `import` run."""

    def __init__(self, context: CleanContext, tally: Tally) -> None:
        """Prepare the copies of a run.

        Args:
            context: Journal (phase `import`), path mapper, progress.
            tally: Counters of the run: one per file copied.
        """
        self._context = context
        self._tally = tally
        self._changes = JournaledChanges(context, tally)

    def run(self, jobs: Sequence[CopyJob], stop: Callable[[], bool]) -> bool:
        """Copy every file; a failure is counted and the run goes on.

        Args:
            jobs: The files.
            stop: Tells when Ctrl+C was pressed: the run stops between two files.

        Returns:
            True when Ctrl+C stopped the run.
        """
        progress = self._context.progress
        progress.start(
            Step(
                _("Copying"), _("Copies each file, then compares it with its source.")
            ),
            len(jobs),
        )
        stopped = False
        for job in jobs:
            if stop():
                stopped = True
                break
            try:
                self._copy(job)
            except OSError as exc:
                _LOGGER.debug("Not copied: %s", job.source, exc_info=True)
                self._tally.failed.append(Incident(job.source, why(exc)))
            progress.advance()
        progress.stop()
        return stopped

    def _copy(self, job: CopyJob) -> None:
        """Journal, copy under a temporary name, prove, rename, journal the digest.

        Args:
            job: The file.

        Raises:
            FileExistsError: A file took the name since the plan (nothing replaced).
        """
        if job.target.exists():
            raise target_exists(job.target)
        make_folders(self._changes, job.target.parent)
        source = file_of(job.source)
        copy = file_of(job.target, (source.size, source.mtime_ns))
        entry = self._changes.entry(copy, ActionKind.COPY_IN)
        entry = entry.model_copy(update={"keeper": str(job.source)})
        journal = self._context.journal
        journal.record(entry)
        digest = _put(job, source.mtime_ns)
        journal.record(entry.as_done().model_copy(update={"sha256": digest}))
        self._changes.count(source.size)


def _put(job: CopyJob, mtime_ns: int) -> str:
    """Copy, prove, then give the copy its name and the source's time.

    Args:
        job: The file.
        mtime_ns: The source's modification time.

    Returns:
        The SHA-256 of the content, read from the source and from the copy.

    Raises:
        OSError: The copy does not match its source (removed), or the name was
            taken meanwhile (the copy under its temporary name is removed).
    """
    temporary = job.target.with_name(job.target.name + _TEMPORARY)
    try:
        digest = copy_exclusive(job.source, temporary)
        _prove(temporary, digest)
        os.utime(temporary, ns=(mtime_ns, mtime_ns))  # copystat may round it
        rename_no_replace(temporary, job.target)
    except OSError:
        with contextlib.suppress(OSError):
            temporary.unlink()
        raise
    return digest


def _prove(copy: Path, digest: str) -> None:
    """Read the copy back: its SHA-256 must be the source's.

    Args:
        copy: The copy, under its temporary name.
        digest: The source's SHA-256, as read.

    Raises:
        OSError: The copy does not match.
    """
    if full_digest(copy) != digest:
        raise OSError(_("the copy does not match its source"))
