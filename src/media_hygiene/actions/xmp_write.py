"""Write sidecars, journaled: never over a file that appeared, proven by reading back.

A new sidecar is written to a temporary file, then renamed to its name only if that
name is still free. A sidecar of another application is first copied, byte for byte,
into this run's quarantine folder (`undo` puts it back from there), then replaced
atomically, only if it still holds what was read. Each sidecar is read back and parsed
before its journal entry is marked `done`.
"""

from __future__ import annotations

import contextlib
import hashlib
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journaled import JournaledChanges
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.no_overwrite import COPY_INSTEAD, rename_no_replace
from media_hygiene.actions.outcome import Incident, why
from media_hygiene.actions.sort_moves import file_of
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step
from media_hygiene.tags.xmp_doc import XmpError, parse

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally

_LOGGER = logging.getLogger(__name__)
_TEMPORARY: Final = ".media-hygiene.tmp"
_EXCLUSIVE: Final = "xb"


@dataclass(frozen=True, slots=True)
class XmpJob:
    """One sidecar to write: for which photo, where, what, and what was there."""

    photo: Path
    sidecar: Path
    content: bytes
    previous: bytes | None  # None: a new sidecar


def digest(content: bytes) -> str:
    """The SHA-256 of some bytes, as the journal keeps it.

    Args:
        content: The bytes.

    Returns:
        Its hexadecimal digest.
    """
    return hashlib.sha256(content).hexdigest()


class XmpExecutor:
    """Journals and writes the sidecars of one run."""

    def __init__(self, context: CleanContext, tally: Tally) -> None:
        """Prepare the writes of a run.

        Args:
            context: Journal (phase `xmp`), path mapper, quarantine folder, progress.
            tally: Counters of the run: one per sidecar written.
        """
        self._context = context
        self._tally = tally
        self._changes = JournaledChanges(context, tally)

    def run(self, jobs: Sequence[XmpJob], stop: Callable[[], bool]) -> bool:
        """Write every sidecar; a failure is counted and the run goes on.

        Args:
            jobs: The sidecars.
            stop: Tells when Ctrl+C was pressed: the run stops between two files.

        Returns:
            True when Ctrl+C stopped the run.
        """
        progress = self._context.progress
        progress.start(
            Step(_("Writing"), _("Writes the words into the .xmp sidecars.")),
            len(jobs),
        )
        stopped = False
        for job in jobs:
            if stop():
                stopped = True
                break
            try:
                self._write(job)
            except (OSError, XmpError) as exc:
                _LOGGER.debug("Sidecar not written: %s", job.sidecar, exc_info=True)
                self._tally.failed.append(Incident(job.sidecar, why(exc)))
            progress.advance()
        progress.stop()
        return stopped

    def _write(self, job: XmpJob) -> None:
        """Journal, keep the previous sidecar, write, read back.

        Args:
            job: The sidecar.
        """
        kind = ActionKind.CREATE_XMP if job.previous is None else ActionKind.MERGE_XMP
        file = file_of(job.sidecar, (len(job.content), 0))
        update: dict[str, object] = {
            "sha256": digest(job.content),
            "keeper": str(job.photo),
        }
        if job.previous is not None:
            backup = self._context.quarantine_run_dir / self._context.mapper.relative(
                job.sidecar
            )
            _keep(job.previous, backup)
            update["quarantine"] = str(backup)
        entry = self._changes.entry(file, kind).model_copy(update=update)
        self._changes.record(entry, lambda: _put(job, entry))
        self._tally.done += 1
        self._tally.bytes_done += len(job.content)


def _keep(previous: bytes, backup: Path) -> None:
    """Copy the previous sidecar into the quarantine, proven identical.

    Args:
        previous: Its bytes, as read.
        backup: Where to keep them.

    Raises:
        OSError: The copy could not be written whole.
    """
    backup.parent.mkdir(parents=True, exist_ok=True)
    with backup.open(_EXCLUSIVE) as stream:
        stream.write(previous)
        stream.flush()
        os.fsync(stream.fileno())
    if backup.read_bytes() != previous:
        raise OSError(_("the copy of the previous sidecar does not match it"))


def _put(job: XmpJob, entry: JournalEntry) -> None:
    """Write the sidecar, then prove it by reading it back.

    Args:
        job: The sidecar.
        entry: Its journal entry (the digest of the new content).

    Raises:
        OSError: Something appeared or changed at its place, or it reads back
            different.
        XmpError: It does not parse once written.
    """
    temporary = job.sidecar.with_name(job.sidecar.name + _TEMPORARY)
    with temporary.open("wb") as stream:
        stream.write(job.content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if job.previous is None:
            _create(temporary, job)
        else:
            if job.sidecar.read_bytes() != job.previous:
                raise OSError(_("it changed while the words were written: left as is"))
            temporary.replace(job.sidecar)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
    written = job.sidecar.read_bytes()
    if digest(written) != entry.sha256:
        raise OSError(_("it reads back different from what was written"))
    parse(written)


def _create(temporary: Path, job: XmpJob) -> None:
    """Give a new sidecar its name, never over a file of that name.

    Args:
        temporary: The written content.
        job: The sidecar.

    Raises:
        OSError: A file of that name exists.
    """
    try:
        rename_no_replace(temporary, job.sidecar)
    except OSError as exc:
        if exc.errno not in COPY_INSTEAD:
            raise
        with job.sidecar.open(_EXCLUSIVE) as stream:
            stream.write(job.content)
            stream.flush()
            os.fsync(stream.fileno())
