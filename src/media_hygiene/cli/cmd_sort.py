"""`media-hygiene sort`: apply the workbook of `classify`, journaled and undoable."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Annotated

import typer
from rich.markup import escape

from media_hygiene.cli.context import runtime_of, user_errors, warn
from media_hygiene.cli.flows import require_terminal
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.sort_view import (
    show_inputs,
    show_kept_folders,
    show_manifest,
    sort_table,
)
from media_hygiene.console.tables import outcome_table
from media_hygiene.constants import ExitCode
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.sort import SortService
from media_hygiene.services.sort_inputs import find_workbook, load_inputs

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort import Prepared, SortResult

_SHOWN_INCIDENTS = 10


# The options are parameters: the documented exception for Typer commands.
def sort_command(  # pylint: disable=too-many-arguments
    ctx: typer.Context,
    workbook: Annotated[
        str | None,
        typer.Argument(
            help=_(
                "The classify workbook, edited; the latest classify run's by default."
            )
        ),
    ] = None,
    *,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help=_("Do not ask for confirmation (overrides sort.confirm)."),
        ),
    ] = False,
    keep_empty_folders: Annotated[
        bool,
        typer.Option(
            "--keep-empty-folders",
            help=_("Keep the source folders the sort leaves empty."),
        ),
    ] = False,
) -> None:
    """Check the workbook, confirm, then move the files into their folders.

    Args:
        ctx: Typer context holding the runtime.
        workbook: The workbook (host or container path), or None for the latest.
        yes: `--yes`, skip the confirmation.
        keep_empty_folders: `--keep-empty-folders`, no folder is removed.

    Raises:
        typer.Exit: The user declined.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        service = SortService(runtime, NullProgress())
        service.ensure_ready()
        inputs = load_inputs(runtime, find_workbook(runtime, workbook))
        output.title(_("Sort"))
        show_inputs(runtime, inputs)
        prepared = service.prepare(inputs, keep_empty=keep_empty_folders)
        output.show(sort_table(prepared))
        show_kept_folders(runtime, prepared.folders, done=False)
        if not prepared.plan.groups:
            output.success(_("Nothing to move: every file is where the plan puts it."))
            return
        if not _confirm(runtime, prepared, yes=yes):
            output.info(_("Nothing was changed."))
            raise typer.Exit(ExitCode.OK)
        with RichProgress(output.console) as progress, StopRequest() as stop:
            result = SortService(runtime, progress).execute(prepared, stop.requested)
    _show_result(runtime, result)


def _confirm(runtime: Runtime, prepared: Prepared, *, yes: bool) -> bool:
    """Ask before sorting, unless `--yes` or `[sort] confirm = false`.

    Args:
        runtime: Settings, mount points and output.
        prepared: The sort.
        yes: `--yes` was given.

    Returns:
        True when the sort may proceed.

    """
    if yes or not runtime.settings.sort.confirm:
        return True
    require_terminal(sys.stdin)
    plan = prepared.plan
    return runtime.output.confirm(
        _("Move {count} files into {folders} folders?").format(
            count=len(plan.moves), folders=len(plan.folders)
        )
    )


def _show_result(runtime: Runtime, result: SortResult) -> None:
    """Show what the run did, the proof, and how to undo or go on.

    Args:
        runtime: Settings, mount points and output.
        result: The run.
    """
    output, host = runtime.output, runtime.mapper.to_host
    outcome = result.moves.outcome
    title = _("Sort {run_id}").format(run_id=result.run_id)
    output.show(outcome_table(outcome, title))
    for incident in outcome.skipped[:_SHOWN_INCIDENTS]:
        output.warning(escape(f"{host(incident.path)}: {incident.reason}"))
    for incident in outcome.failed[:_SHOWN_INCIDENTS]:
        output.error(escape(f"{host(incident.path)}: {incident.reason}"))
    if result.folders.removed:
        output.info(
            _("Source folders removed: {count}.").format(count=result.folders.removed)
        )
    show_kept_folders(runtime, result.folders, done=True)
    show_manifest(output, result.manifest)
    if isinstance(result.manifest_file, MediaHygieneError):
        warn(output, result.manifest_file)
    elif result.manifest_file is not None:
        output.info(_("Manifest: {path}").format(path=host(result.manifest_file)))
    if result.moves.interrupted:
        output.warning(_("Stopped before the end, as asked."))
        output.tip(
            _("Run the same command again to continue: the files moved are skipped.")
        )
    output.tip(
        _(
            "Changed your mind? 'media-hygiene undo {run_id}' moves everything back."
        ).format(run_id=result.run_id)
    )
