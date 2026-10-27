"""`purge --to <folder>`: copy each run, prove the copy, then erase it (0306)."""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.archive_copy import (
    Archived,
    ArchiveError,
    ArchiveJob,
    archive_run,
    missing_space,
)
from media_hygiene.actions.archived import archive_record, note_archived
from media_hygiene.actions.purge import folder_size
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime

_DEFAULT_DRIVE = "C"  # the default quarantine is C:'s with `mh`


@dataclass(frozen=True, slots=True)
class PurgeQuestion:
    """What the confirmation of a purge names."""

    runs: tuple[str, ...]
    count: str
    size: str
    target: Path | None
    yes: bool


def purge_question(runtime: Runtime, asked: PurgeQuestion) -> str:
    """Build the question; without a target, warn first and show `--to`.

    Args:
        runtime: Settings, mount points and output.
        asked: The runs, their count and size, the target.

    Returns:
        The question to confirm.
    """
    runs = ", ".join(asked.runs)
    if asked.target is not None:
        return _(
            "Copy the quarantine of {runs} ({count} files, {size}) to {target}, "
            "check the copy, then empty it?"
        ).format(runs=runs, count=asked.count, size=asked.size, target=asked.target)
    runtime.output.warning(
        _(
            "'purge' erases for good: these files cannot come back, not even with "
            "'undo'. It is, with 'clean --delete', the only way the tool removes "
            "content."
        )
    )
    if not asked.yes:  # a script: nobody reads it
        show_archive_hint(runtime)
    return _("Erase the quarantine of {runs} ({count} files, {size})?").format(
        runs=runs, count=asked.count, size=asked.size
    )


def show_archive_hint(runtime: Runtime) -> None:
    """Tell, before the question, that a copy can be kept elsewhere instead.

    Args:
        runtime: Settings, mount points and output.
    """
    runtime.output.info(
        _(
            "Rather keep a copy elsewhere? 'purge --to <folder>' first copies the "
            "quarantine there, checks every byte of the copy, and only then empties "
            "the quarantine. <folder> can be a NAS share, an external disk or a "
            "cloud's synced folder, mounted in the container."
        )
    )


def refuse_target(runtime: Runtime, target: Path) -> Path:
    """Stop when the target is, holds or lies in a photo or tool folder.

    Args:
        runtime: Settings, mount points and output.
        target: The `--to` folder.

    Returns:
        The target, made absolute.

    Raises:
        MediaHygieneError: It overlaps one of them.
    """
    resolved = target.resolve()
    locations = runtime.locations
    guarded = {locations.path_of(kind).resolve() for kind in MountKind}
    guarded |= {folder.resolve() for folder in mounted_quarantines(runtime).folders}
    for folder in sorted(guarded):
        if resolved.is_relative_to(folder) or folder.is_relative_to(resolved):
            raise MediaHygieneError(
                _(
                    "The archive folder {target} and {folder} are one inside the other."
                ).format(target=resolved, folder=folder),
                _("Archive to a folder of its own (a NAS, another disk)."),
            )
    return resolved


def archive_runs(runtime: Runtime, runs: list[str], target: Path) -> list[Archived]:
    """Copy every run to the target and prove each copy; erase nothing.

    Args:
        runtime: Settings, mount points and output.
        runs: The runs.
        target: The checked `--to` folder.

    Returns:
        What the target holds of each run, read back from it.

    Raises:
        MediaHygieneError: Not enough space, or a copy failed or differs.
    """
    jobs = [_job(runtime, run, target) for run in runs]
    needed = sum(folder_size(folder) for job in jobs for _label, folder in job.sources)
    missing = missing_space(target, needed)
    if missing:
        raise MediaHygieneError(
            _(
                "{target} lacks {missing} for the copy: nothing copied, nothing erased."
            ).format(target=target, missing=human_size(missing))
        )
    done: list[Archived] = []
    for job in jobs:
        try:
            done.append(archive_run(job))
        except ArchiveError as exc:
            raise MediaHygieneError(
                str(exc), _("Run {run} stays in the quarantine.").format(run=job.run)
            ) from exc
        note_archived(
            runtime.locations.journal_dir, archive_record(job.run, str(target))
        )
    return done


def _job(runtime: Runtime, run: str, target: Path) -> ArchiveJob:
    """The folders of a run, labelled by drive.

    Args:
        runtime: Settings, mount points and output.
        run: The run.
        target: The archive folder.

    Returns:
        The job.
    """
    quarantines = mounted_quarantines(runtime)
    labelled = [(_DEFAULT_DRIVE, quarantines.default)]
    labelled += [(drive.rstrip(":"), folder) for drive, folder in quarantines.by_drive]
    sources = tuple(
        (label, folder / run) for label, folder in labelled if (folder / run).is_dir()
    )
    return ArchiveJob(run, sources, target)


def report_archived(runtime: Runtime, archived: list[Archived]) -> None:
    """Show what each target folder holds, then how to get a run back.

    Args:
        runtime: Settings, mount points and output.
        archived: What was read back from the target.
    """
    output = runtime.output
    for copy in archived:
        output.info(
            _("Archived: {count} files, {size} in {folder}.").format(
                count=human_number(copy.files),
                size=human_size(copy.size),
                folder=copy.folder,
            )
        )
    output.next_step(
        _(
            "To get a run back: copy each drive's folder of it back into that drive's "
            "quarantine, then run 'undo <run>'."
        )
    )
