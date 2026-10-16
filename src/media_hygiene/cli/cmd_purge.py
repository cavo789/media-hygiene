"""`media-hygiene purge`: erase the quarantine for good — the one way content goes."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _

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
        MediaHygieneError: The requested run has no quarantine, the quarantine is
            not writable, or it has files in the quarantine of a drive not mounted
            now (nothing is erased; without a run named, such runs are kept).
        typer.Exit: The user declined.
    """
    from media_hygiene.actions.purge import (
        file_count,
        folder_size,
        run_folders,
        runs_in,
    )
    from media_hygiene.console.formatting import human_number, human_size
    from media_hygiene.errors import MediaHygieneError
    from media_hygiene.paths.mount_kind import MountKind
    from media_hygiene.services.quarantines import (
        held_back,
        mounted_quarantines,
        refuse_unplugged,
    )
    from media_hygiene.services.tool_mounts import refuse_tool_folders_in_data
    from media_hygiene.services.writable import ensure_writable

    runtime = runtime_of(ctx)
    output = runtime.output
    quarantines = mounted_quarantines(runtime).folders
    with user_errors(output):
        ensure_writable(runtime, MountKind.QUARANTINE)
        refuse_tool_folders_in_data(runtime, (MountKind.QUARANTINE,))
        runs = runs_in(quarantines)
        if run_id is not None:
            refuse_unplugged(runtime, [run_id])  # some or all of it on a drive gone
            if run_id not in runs:
                raise MediaHygieneError(
                    _("Run {run_id} has no quarantine.").format(run_id=run_id)
                )
            runs = [run_id]
    held = held_back(runtime, runs)  # each run whole, or not at all (0183)
    if held:
        output.warning(
            _(
                "Kept, their drive's quarantine not mounted: {runs}. Plug the drive "
                "in, then purge them."
            ).format(runs=", ".join(f"{run} ({drive})" for run, drive in held.items()))
        )
        runs = [run for run in runs if run not in held]
    if not runs:
        if not held:
            output.info(_("The quarantine is empty."))
        return
    folders = [folder for run in runs for folder in run_folders(quarantines, run)]
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
    """Erase the quarantine of each run, on every drive.

    Args:
        runtime: Settings, mount points and output.
        runs: The runs.

    Returns:
        Bytes freed.

    Raises:
        MediaHygieneError: A folder could not be erased (what is left stays).
    """
    from media_hygiene.actions.purge import purge_run, run_folders
    from media_hygiene.errors import MediaHygieneError
    from media_hygiene.index.parked import forget_runs
    from media_hygiene.index.repository import FactsRepository
    from media_hygiene.services.quarantines import mounted_quarantines

    quarantines = mounted_quarantines(runtime).folders
    try:
        freed = sum(
            purge_run(folder.parent, run)
            for run in runs
            for folder in run_folders(quarantines, run)
        )
    except OSError as exc:
        raise MediaHygieneError(
            _("The quarantine could not be erased: {reason}.").format(
                reason=exc.strerror or exc
            ),
            _("What is left stays in the quarantine; run 'purge' again later."),
        ) from exc
    index = runtime.index_file
    if index is not None and index.is_file():  # what the index kept of them (0156)
        with FactsRepository.open(index) as repository:
            forget_runs(repository.connection, runs)
    return freed
