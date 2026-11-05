"""Write a day into the sidecars of some photos (0531): `xmp`'s journal, its undo."""

from __future__ import annotations

from dataclasses import dataclass
from importlib.metadata import version
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.xmp_write import XmpJob
from media_hygiene.constants import APP_NAME
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.host_paths import is_within
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.xmp import XmpService
from media_hygiene.services.xmp_plan import XmpPlan
from media_hygiene.services.xmp_sidecars import sidecar_of
from media_hygiene.tags.xmp_date import with_day
from media_hygiene.tags.xmp_doc import XmpError

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class DateJobs:
    """The sidecars to write, and the photos left."""

    jobs: tuple[XmpJob, ...]
    protected: int = 0
    theirs: int = 0  # another application's date, or a sidecar that cannot be read


@dataclass(frozen=True, slots=True)
class DatesWritten:
    """What a run did: its identifier (empty: none), and what it left."""

    run: str
    failed: int
    asked: DateJobs

    def undo_line(self) -> str:
        """The way back, as the CLI teaches it.

        Returns:
            The line.
        """
        return _("'mh undo {run}' takes it back.").format(run=self.run)

    def notes(self, own: int) -> list[str]:
        """The sentences on the files left.

        Args:
            own: Those with a date of their own.

        Returns:
            One sentence per reason.
        """
        told = (
            (
                own,
                ngettext(
                    "{n} has its own date: left.", "{n} have their own date: left.", own
                ),
            ),
            (
                self.asked.protected,
                ngettext(
                    "{n} in a protected folder: left.",
                    "{n} in a protected folder: left.",
                    self.asked.protected,
                ),
            ),
            (
                self.asked.theirs,
                ngettext(
                    "{n} sidecar of another application: left.",
                    "{n} sidecars of another application: left.",
                    self.asked.theirs,
                ),
            ),
            (
                self.failed,
                ngettext(
                    "{n} could not be written.",
                    "{n} could not be written.",
                    self.failed,
                ),
            ),
        )
        return [line.format(n=count) for count, line in told if count]


@dataclass(frozen=True, slots=True)
class DateWriter:
    """Writes the sidecars, with the guards of every command that changes files."""

    runtime: Runtime

    def ensure_ready(self) -> None:
        """Refuse without a journal, or on read-only folders."""
        ensure_can_act(self.runtime, Phase.XMP.value)

    def jobs(self, photos: tuple[Path, ...], day: str) -> DateJobs:
        """Decide each sidecar.

        Args:
            photos: The photos.
            day: `YYYY-MM-DD`.

        Returns:
            The sidecars to write; a protected folder is never written.
        """
        runtime = self.runtime
        untouched = tuple(
            map(runtime.mapper.to_container, runtime.settings.folders.untouched)
        )
        tool = f"{APP_NAME} {version(APP_NAME)}"
        folders: dict[Path, list[str]] = {}
        jobs: list[XmpJob] = []
        protected = theirs = 0
        for photo in photos:
            if any(is_within(photo, folder) for folder in untouched):
                protected += 1
                continue
            job = _job(photo, day, (tool, folders))
            if job is None:
                theirs += 1
            elif job.content != job.previous:
                jobs.append(job)
        return DateJobs(tuple(jobs), protected, theirs)

    def write(self, asked: DateJobs) -> DatesWritten:
        """Write them under a new run.

        Args:
            asked: The sidecars.

        Returns:
            The run; none when nothing was to write.
        """
        if not asked.jobs:
            return DatesWritten("", 0, asked)
        service = XmpService(self.runtime, NullProgress())
        done = service.execute(XmpPlan(jobs=list(asked.jobs)), lambda: False)
        return DatesWritten(done.run_id, len(done.outcome.failed), asked)


def _job(
    photo: Path, day: str, made: tuple[str, dict[Path, list[str]]]
) -> XmpJob | None:
    """The sidecar of one photo, holding this day.

    Args:
        photo: The photo.
        day: `YYYY-MM-DD`.
        made: The tool's name, and the names of each folder listed so far.

    Returns:
        The job; None for another application's date, or a sidecar that cannot be read.
    """
    tool, folders = made
    try:
        sidecar = sidecar_of(photo, folders)
        previous = sidecar.read_bytes() if sidecar.is_file() else None
        content = with_day(previous, day, tool)
    except OSError, XmpError:
        return None
    return None if content is None else XmpJob(photo, sidecar, content, previous)
