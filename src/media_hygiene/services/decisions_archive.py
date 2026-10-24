"""`clean --decisions`: once applied, the decisions file is archived, never deleted.

After the clean, the shots set aside sit in the quarantine: the file no longer matches
the folders, so `clean --decisions` would refuse it and `review` would drop its series.
It is renamed `<name>.applied-<run>.json` beside itself: the next `review` starts
afresh, and after an `undo` the archive applies the same choices again. Asked again
once applied, `clean --decisions` finds the archive and says so: nothing is left to do.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.place import decisions_flag, decisions_place
from media_hygiene.services.review import decisions_path

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_APPLIED: Final = ".applied-"  # between the name and the run of an archive


def archive_decisions(runtime: Runtime, source: Path, run_id: str) -> None:
    """Rename the applied decisions file after the clean run, and say where it went.

    The rename is read back from the disk before it is announced; a failure only
    warns: the clean itself is done.

    Args:
        runtime: Settings, mount points and output.
        source: `--decisions` value.
        run_id: The clean run that applied it.
    """
    target = decisions_path(runtime, source)
    archive = target.with_name(f"{target.stem}{_APPLIED}{run_id}{target.suffix}")
    output = runtime.output
    try:
        target.rename(archive)
    except OSError as exc:
        message = _("The decisions file {file} could not be archived ({error}).")
        output.warning(message.format(file=target.name, error=exc.strerror or exc))
        return
    if target.exists() or not archive.is_file():
        message = _("The decisions file {file} could not be archived.")
        output.warning(message.format(file=target.name))
        return
    place = decisions_place(runtime.mapper, runtime.locations.reports_dir, archive)
    applied = _(
        "📦 {file} is applied: archived as {archive}, the next 'review' starts afresh."
    )
    output.info(applied.format(file=target.name, archive=place.host))
    again = _("After an undo, 'media-hygiene clean {flag}' applies it again.")
    output.tip(again.format(flag=decisions_flag(place.argument)))


def applied_before(runtime: Runtime, source: Path) -> Path | None:
    """Find the archive of a decisions file that is gone because a clean applied it.

    Args:
        runtime: Settings, mount points and output.
        source: `--decisions` value.

    Returns:
        The newest archive, or None when the file is there or was never applied.
    """
    target = decisions_path(runtime, source)
    return None if target.exists() else newest_archive(target)


def newest_archive(target: Path) -> Path | None:
    """Find the newest archive of a decisions file, whether the file is there or not.

    Run IDs are timestamps: the last archive by name is the newest.

    Args:
        target: The decisions file, in the container.

    Returns:
        The newest archive, or None when it was never applied.
    """
    archives = sorted(target.parent.glob(f"{target.stem}{_APPLIED}*{target.suffix}"))
    return archives[-1] if archives else None


def tell_applied(runtime: Runtime, archive: Path) -> None:
    """Say that the decisions were applied already: nothing is wrong, nothing to do.

    Args:
        runtime: Settings, mount points and output.
        archive: The newest archive (`applied_before`).
    """
    run_id = archive.stem.rpartition(_APPLIED)[2]
    place = decisions_place(runtime.mapper, runtime.locations.reports_dir, archive)
    message = _(
        "Nothing left to apply: your decisions were applied by the clean {run_id} "
        "(archived as {archive}). Nothing was changed."
    )
    runtime.output.success(message.format(run_id=run_id, archive=place.host))
