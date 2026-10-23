"""Lighten videos one at a time: encode beside, prove, set the original aside, rename.

Each video is re-encoded under a temporary name next to it (same drive), proven
(`shrink.check`), and kept only when it is at least `min_gain_percent` percent lighter;
otherwise it is thrown away and the original remembered as not worth it (a journal
mark). A kept one: the original goes to its drive's quarantine (journaled, remembered:
a phone's copy of it is never imported again), the lighter video takes the name with
`.mp4` and the original's modification time, then a sidecar named after the whole
file follows (`shrink_sidecars`). `undo` removes it while it holds what was
written, then brings the original back.
"""

from __future__ import annotations

import contextlib
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.job_loop import JobLoop
from media_hygiene.actions.journaled import JournaledChanges, Origin
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.no_overwrite import rename_no_replace
from media_hygiene.actions.shrink_sidecars import follow_sidecars
from media_hygiene.actions.sort_moves import file_of, target_exists
from media_hygiene.i18n import _
from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.progress import Step
from media_hygiene.shrink.check import flaw, refuse
from media_hygiene.shrink.encode import encode, ffmpeg_command

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.shrink.candidates import Candidate
    from media_hygiene.shrink.check import Tools
    from media_hygiene.shrink.encode import Encoding

MP4: Final = ".mp4"
_TEMPORARY: Final = ".media-hygiene.tmp"
_PERCENT: Final = 100


@dataclass(frozen=True, slots=True)
class Recipe:
    """How the videos are re-encoded, with which tools, and the gain required."""

    encoding: Encoding
    tools: Tools
    min_gain_percent: int


@dataclass(slots=True)
class Gains:
    """What a run saved, and the videos not worth it."""

    saved: int = 0
    not_worth: int = 0


class ShrinkExecutor:
    """Journals and lightens the videos of one `shrink` run."""

    def __init__(self, context: CleanContext, tally: Tally, recipe: Recipe) -> None:
        """Prepare a run, journaled under the phase `shrink`.

        Args:
            context: Where to journal, set aside and report progress.
            tally: Counters: one per original set aside, its bytes.
            recipe: The encoding, the tools and the gain required.
        """
        self._changes = JournaledChanges(context, tally)
        self._context = context
        self._tally = tally
        self._recipe = recipe
        self.gains = Gains()

    def run(self, jobs: Sequence[Candidate], stop: Callable[[], bool]) -> bool:
        """Lighten every video; one that fails is counted, the others go on.

        Args:
            jobs: The videos.
            stop: Tells when Ctrl+C was pressed: the video being encoded ends first.

        Returns:
            True when Ctrl+C stopped the run.
        """
        step = Step(
            _("Lightening"),
            _("Re-encodes each video, then checks it before keeping it."),
        )
        loop = JobLoop(self._context.progress, step, self._tally, self._one, _path)
        return loop.run(jobs, stop)

    def _one(self, job: Candidate) -> None:
        """Encode, prove, weigh, then keep the lighter video or throw it away.

        Args:
            job: The video.

        Raises:
            ValueError: It changed since the audit, or the result lost something.
            FileExistsError: Another file has the name the lighter video would take.
        """
        file = file_of(job.path)
        if (file.size, file.mtime_ns) != (job.size, job.mtime_ns):
            raise ValueError(_("it changed since the audit: audit again"))
        final = job.path.with_suffix(MP4)
        if final != job.path and final.exists():
            raise target_exists(final)
        temporary = final.with_name(final.name + _TEMPORARY)
        self._context.progress.current(job.path.name)
        after = self._encoded(job, temporary)
        if after > job.size * (_PERCENT - self._recipe.min_gain_percent) / _PERCENT:
            temporary.unlink()
            entry = self._changes.entry(file, ActionKind.MARK_NOT_WORTH)
            self._changes.record(entry, lambda: None)
            self.gains.not_worth += 1
            return
        os.utime(temporary, ns=(file.mtime_ns, file.mtime_ns))
        self._changes.quarantine(file, ActionKind.QUARANTINE_SHRUNK, Origin(final))
        self._put(file, temporary, final)
        self.gains.saved += job.size - after
        follow_sidecars(self._changes, self._tally.skipped, (job.path, final))

    def _encoded(self, job: Candidate, temporary: Path) -> int:
        """Encode under the temporary name and prove the result.

        Args:
            job: The video.
            temporary: Where the result is written.

        Returns:
            The size of the result.

        Raises:
            ValueError: The encoding failed or the result lost something (removed).
        """
        recipe = self._recipe
        command = ffmpeg_command(
            recipe.tools.ffmpeg, (job.path, temporary), recipe.encoding
        )
        try:
            refuse(
                encode(command, job.duration)
                or flaw((job.path, temporary), recipe.tools)
            )
            return temporary.stat().st_size
        except OSError, ValueError:
            with contextlib.suppress(OSError):
                temporary.unlink()
            raise

    def _put(self, original: MediaFile, temporary: Path, final: Path) -> None:
        """Give the lighter video its name, journaled with its SHA-256.

        Args:
            original: The video set aside.
            temporary: The proven result.
            final: Its name.
        """
        stat = (temporary.stat().st_size, original.mtime_ns)
        entry = self._changes.entry(file_of(final, stat), ActionKind.SHRUNK)
        entry = entry.model_copy(update={"keeper": str(original.path)})
        journal = self._context.journal
        journal.record(entry)
        try:
            rename_no_replace(temporary, final)
        except OSError as exc:
            message = _(
                "the lighter video stays as {name} ({error}); the original is in "
                "the quarantine: 'undo' brings it back"
            )
            raise ValueError(message.format(name=temporary.name, error=exc)) from exc
        journal.record(
            entry.as_done().model_copy(update={"sha256": full_digest(final)})
        )


def _path(job: Candidate) -> Path:
    """The file a failure is told about.

    Args:
        job: The video.

    Returns:
        Its path.
    """
    return job.path
