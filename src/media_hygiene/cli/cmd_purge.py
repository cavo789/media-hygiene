"""`media-hygiene purge`: erase the quarantine for good — the one way content goes."""

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.actions.purge import (
    file_count,
    folder_size,
    purge_run,
    quarantine_runs,
)
from media_hygiene.cli import options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.console.formatting import human_number, human_size
from media_hygiene.constants import ExitCode
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.tool_mounts import refuse_tool_folders_in_data
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime


def purge_command(
    ctx: typer.Context,
    run_id: Annotated[
        str | None,
        typer.Argument(help=_("Run whose quarantine is erased; every run by default.")),
    ] = None,
    *,
    yes: Annotated[bool, options.yes()] = False,
) -> None:
    """Free the space held by the quarantine — this cannot be undone.

    Args:
        ctx: Typer context holding the runtime.
        run_id: Run to purge, or None for every run.
        yes: `--yes`, skip the confirmation.

    Raises:
        MediaHygieneError: The requested run has no quarantine, or the quarantine is
            not writable.
        typer.Exit: The user declined.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    quarantine_dir = runtime.locations.quarantine_dir
    with user_errors(output):
        ensure_writable(runtime, MountKind.QUARANTINE)
        refuse_tool_folders_in_data(runtime, (MountKind.QUARANTINE,))
        runs = quarantine_runs(quarantine_dir)
        if run_id is not None:
            if run_id not in runs:
                raise MediaHygieneError(
                    _("Run {run_id} has no quarantine.").format(run_id=run_id)
                )
            runs = [run_id]
    if not runs:
        output.info(_("The quarantine is empty."))
        return
    folders = [quarantine_dir / run for run in runs]
    count = sum(file_count(folder) for folder in folders)
    size = human_size(sum(folder_size(folder) for folder in folders))
    output.warning(
        _(
            "'purge' erases for good: these files cannot come back, not even with "
            "'undo'. It is, with 'clean --delete', the only way the tool removes "
            "content."
        )
    )
    question = _("Erase the quarantine of {runs} ({count} files, {size})?")
    asked = question.format(runs=", ".join(runs), count=human_number(count), size=size)
    if not yes and not output.confirm(asked):
        output.info(_("Nothing was changed."))
        raise typer.Exit(ExitCode.OK)
    with user_errors(output):
        freed = _purge(runtime, runs)
    output.success(_("Quarantine purged: {size} freed.").format(size=human_size(freed)))
    output.tip(_("'undo' can no longer restore these files."))


def _purge(runtime: Runtime, runs: list[str]) -> int:
    """Erase the quarantine of each run.

    Args:
        runtime: Settings, mount points and output.
        runs: The runs.

    Returns:
        Bytes freed.

    Raises:
        MediaHygieneError: A folder could not be erased (what is left stays).
    """
    quarantine_dir = runtime.locations.quarantine_dir
    try:
        return sum(purge_run(quarantine_dir, run) for run in runs)
    except OSError as exc:
        raise MediaHygieneError(
            _("The quarantine could not be erased: {reason}.").format(
                reason=exc.strerror or exc
            ),
            _("What is left stays in the quarantine; run 'purge' again later."),
        ) from exc
