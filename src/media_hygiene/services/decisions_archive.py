"""`clean --decisions`: once applied, the decisions file is archived, never deleted.

After the clean, the shots set aside sit in the quarantine: the file no longer matches
the folders, so `clean --decisions` would refuse it and `review` would drop its series.
It is renamed `<name>.applied-<run>.json` beside itself: the next `review` starts
afresh, and after an `undo` the archive applies the same choices again.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.review.place import decisions_flag, decisions_place
from media_hygiene.services.review import decisions_path

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime


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
    archive = target.with_name(f"{target.stem}.applied-{run_id}{target.suffix}")
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
