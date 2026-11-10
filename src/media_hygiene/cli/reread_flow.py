"""`audit --reread` and `clean --repair`: the damaged files in the console (0690)."""

# pylint: disable=import-outside-toplevel  # lazy: imported by `clean` at start-up

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.cli.context import user_errors
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.services.good_copy import Repairable
    from media_hygiene.services.runtime import Runtime


def reread_and_list(runtime: Runtime) -> None:
    """Read again within the budget, then list every damaged file. Changes nothing.

    Args:
        runtime: Settings, mount points and output.
    """
    from media_hygiene.services.good_copy import repairables  # noqa: PLC0415
    from media_hygiene.services.reread import reread  # noqa: PLC0415

    output = runtime.output
    output.info(
        _("Reading again up to {gb} GB, the files read longest ago first…").format(
            gb=runtime.settings.routine.reread_gb
        )
    )
    result = reread(runtime)
    output.success(
        _("{count} files read again ({size}).").format(
            count=human_number(result.files), size=human_size(result.bytes_read)
        )
    )
    found = repairables(runtime)
    if not found:
        output.success(_("No damaged file known. 🔒 Nothing was changed."))
        return
    show_damaged(runtime, found)
    if any(item.copy is not None for item in found):
        output.next_step(
            _("restore them from their good copy (listed again, then asked):"),
            "mh clean --repair",
        )


def show_damaged(runtime: Runtime, found: Sequence[Repairable]) -> None:
    """List each damaged file, since when, and its good copy.

    Args:
        runtime: Mount points and output.
        found: The damaged files.
    """
    output, host = runtime.output, runtime.mapper.to_host
    output.warning(
        ngettext(
            "{count} file changed while its size and date did not: damaged, or "
            "rewritten by a program that kept its date — look.",
            "{count} files changed while their size and date did not: damaged, or "
            "rewritten by a program that kept their date — look.",
            len(found),
        ).format(count=human_number(len(found)))
    )
    for item in found:
        row = item.damaged
        output.info(
            _("{path}: found changed on {since}, read fine on {good}.").format(
                path=host(Path(row.path)),
                since=row.damaged_since[:10],
                good=row.verified_at[:10],
            )
        )
        output.info("   " + _copy_line(runtime, item))


def _copy_line(runtime: Runtime, item: Repairable) -> str:
    """Where the good copy is.

    Args:
        runtime: Mount points.
        item: The damaged file.

    Returns:
        The line.
    """
    from media_hygiene.services.good_copy import CopyPlace  # noqa: PLC0415

    if item.copy is None:
        return _("no good copy found here: look on your backup (NAS, disk).")
    where = runtime.mapper.to_host(item.copy)
    if item.place is CopyPlace.QUARANTINE:
        return _("good copy in the quarantine: {path}").format(path=where)
    return _("good copy: {path}").format(path=where)


def repair_flow(runtime: Runtime, yes: bool) -> int:  # noqa: FBT001 - a CLI flag
    """List the files to restore, ask, restore, then show what was read back.

    Args:
        runtime: Settings, mount points and output.
        yes: `--yes`, no question.

    Returns:
        How many files were proven restored.
    """
    from media_hygiene.console.progress import RichProgress  # noqa: PLC0415
    from media_hygiene.services.good_copy import repairables  # noqa: PLC0415
    from media_hygiene.services.repair import jobs_of, repair  # noqa: PLC0415

    output = runtime.output
    found = repairables(runtime)
    jobs = jobs_of(found)
    if not jobs:
        output.info(
            _(
                "Nothing to restore: no damaged file with a good copy "
                "('audit --reread')."
            )
        )
        return 0
    show_damaged(runtime, found)
    question = _(
        "Restore these {count} files from their good copy? The damaged ones go to "
        "the quarantine."
    ).format(count=human_number(len(jobs)))
    if not yes and not output.confirm(question):
        return 0
    with RichProgress(output.console) as progress:
        result = repair(runtime, jobs, progress)
    for path in result.proven:
        output.success(
            _("Restored, read back: {path}").format(path=runtime.mapper.to_host(path))
        )
    for incident in result.outcome.failed:
        output.warning(f"{runtime.mapper.to_host(incident.path)}: {incident.reason}")
    output.info(
        _("Undo: mh undo {run} (the damaged files come back).").format(
            run=result.run_id
        )
    )
    return len(result.proven)


def repair_if_asked(runtime: Runtime, asked: bool, yes: bool) -> bool:  # noqa: FBT001
    """Run `clean --repair` when asked, instead of a clean.

    Args:
        runtime: Settings, mount points and output.
        asked: `--repair`.
        yes: `--yes`, no question.

    Returns:
        True when it ran: the clean itself does not.
    """
    if asked:
        with user_errors(runtime.output):
            repair_flow(runtime, yes)
    return asked
