"""Turn photos, journaled: two EXIF orientation bytes, proven by reading back (0802).

Each photo is read, its new bytes made by `orientation_bytes.with_orientation` (no
re-encode), journaled `pending` with the SHA-256 and code before and the SHA-256
after, written to a temporary file then renamed over the photo only if it still holds
what was read, read back, then marked `done`. The photo gets a new modification time:
the index sees a new version (its digests are computed again), and `undo` puts the old
time back with the old bytes.
"""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.job_loop import JobLoop
from media_hygiene.actions.journaled import JournaledChanges
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.orientation_bytes import with_orientation
from media_hygiene.actions.sort_moves import file_of
from media_hygiene.actions.xmp_write import digest
from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally

_TEMPORARY: Final = ".media-hygiene.turn"


@dataclass(frozen=True, slots=True)
class TurnJob:
    """One photo to turn: its path and the EXIF orientation code to give it."""

    path: Path
    code: int


def put_bytes(path: Path, content: bytes, before: bytes) -> None:
    """Replace a file's bytes atomically, only if it still holds `before`.

    Args:
        path: The file.
        content: Its new bytes.
        before: What it held when read.

    Raises:
        OSError: It changed meanwhile, or reads back different.
    """
    temporary = path.with_name(path.name + _TEMPORARY)
    with temporary.open("wb") as stream:
        stream.write(content)
        stream.flush()
        os.fsync(stream.fileno())
    try:
        if path.read_bytes() != before:
            raise OSError(_("it changed while it was turned: left as is"))
        temporary.replace(path)
    finally:
        with contextlib.suppress(FileNotFoundError):
            temporary.unlink()
    if path.read_bytes() != content:
        raise OSError(_("it reads back different from what was written"))


class TurnExecutor:
    """Journals and writes the turns of one run."""

    def __init__(self, context: CleanContext, tally: Tally) -> None:
        """Prepare the writes of a run.

        Args:
            context: Journal (phase `turn`), path mapper, progress.
            tally: Counters of the run: one per photo turned.
        """
        self._changes = JournaledChanges(context, tally)
        self._progress = context.progress
        self._tally = tally

    def run(self, jobs: Sequence[TurnJob], stop: Callable[[], bool]) -> bool:
        """Turn the photos one by one; one failing is counted, the others go on.

        Args:
            jobs: The photos and their codes.
            stop: True once Ctrl+C was pressed: nothing more after this photo.

        Returns:
            Whether Ctrl+C ended the run early.
        """
        step = Step(_("Turning"), _("Changes the orientation tag of the photos."))
        loop = JobLoop(self._progress, step, self._tally, self._turn, _path_of)
        return loop.run(jobs, stop)

    def _turn(self, job: TurnJob) -> None:
        """Read, journal, write, read back.

        Args:
            job: The photo.
        """
        info = job.path.stat()
        before = job.path.read_bytes()
        after, code = with_orientation(before, job.code)
        file = file_of(job.path, (info.st_size, info.st_mtime_ns))
        update = {"sha256": digest(after), "orientation": (code, digest(before))}
        entry = self._changes.entry(file, ActionKind.TURN).model_copy(update=update)
        self._changes.record(entry, lambda: put_bytes(job.path, after, before))
        self._tally.done += 1


def _path_of(job: TurnJob) -> Path:
    """The photo a job turns, as the progress and failures name it.

    Args:
        job: The job.

    Returns:
        Its path.
    """
    return job.path
