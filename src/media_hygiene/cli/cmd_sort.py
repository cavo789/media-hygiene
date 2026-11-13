"""`media-hygiene sort`: apply the workbook of `classify`, journaled and undoable."""

# pylint: disable=import-outside-toplevel,too-many-locals  # lazy: a command imports
# the code it runs when it runs; those imports count as local variables.

from __future__ import annotations

import sys
from functools import partial
from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli import folder_options
from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_models import Prepared


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
    event: Annotated[
        str,
        typer.Option(
            "--event",
            help=_(
                "Sort only the files of this event (its id: the first column of the "
                "Events sheet); the rest of the workbook is left for later."
            ),
        ),
    ] = "",
    trial: Annotated[
        str,
        typer.Option(
            "--trial",
            help=_(
                "Sort a sample first: 'latest' (the latest month with photos), a "
                "month such as 2024-05, or a folder; the same sort then does the rest."
            ),
        ),
    ] = "",
    backup: Annotated[list[str] | None, folder_options.kept_backup()] = None,
) -> None:
    """Check the workbook, confirm, then move the files into their folders.

    Args:
        ctx: Typer context holding the runtime.
        backup: `--backup` folders, read-only on purpose: never refused (0262).
        workbook: The workbook (host or container path), or None for the latest.
        yes: `--yes`, skip the confirmation.
        keep_empty_folders: `--keep-empty-folders`, no folder is removed.
        event: `--event`, only the files of this event.
        trial: `--trial`, only a sample: a month or a folder (0526); without it, a
            first sort offers the latest month first (0640).

    Raises:
        typer.Exit: The user declined.
    """
    from media_hygiene.cli.sort_offer import offer_trial
    from media_hygiene.cli.sort_result import show_result
    from media_hygiene.console.progress import RichProgress
    from media_hygiene.console.sort_view import (
        show_follows,
        show_inputs,
        show_kept_folders,
        sort_table,
    )
    from media_hygiene.scan.progress import NullProgress
    from media_hygiene.services.interrupt import StopRequest
    from media_hygiene.services.sort import SortService
    from media_hygiene.services.sort_event import only_event
    from media_hygiene.services.sort_inputs import find_workbook, load_inputs
    from media_hygiene.services.sort_trial import LATEST, only_trial

    runtime = runtime_of(ctx).with_overrides(folder_options.backup_layer(backup))
    output = runtime.output
    with user_errors(output):
        service = SortService(runtime, NullProgress())
        service.ensure_ready()
        inputs = load_inputs(runtime, find_workbook(runtime, workbook))
        if event:
            inputs = only_event(inputs, event)
        if trial:
            inputs = only_trial(inputs, trial, runtime.mapper)
        output.title(_("Sort"))
        show_inputs(runtime, inputs)
        prepared = service.prepare(inputs, keep_empty=keep_empty_folders)
        output.show(sort_table(prepared))
        show_follows(output, prepared.plan)
        show_kept_folders(runtime, prepared.folders, done=False)
        if not prepared.plan.groups:
            output.success(_("Nothing to move: every file is where the plan puts it."))
            return
        output.info(
            _(
                "🛟 Each file is moved, never over another one nor deleted; the run "
                "is journaled: 'undo' puts everything back."
            )
        )
        sample = (
            None
            if yes or trial or event
            else offer_trial(
                runtime,
                prepared,
                partial(service.prepare, keep_empty=keep_empty_folders),
            )
        )
        if sample is not None:
            prepared, trial = sample, LATEST
        elif not _confirm(runtime, prepared, yes=yes):
            output.info(_("Nothing was changed."))
            raise typer.Exit(ExitCode.OK)
        with RichProgress(output.console) as progress, StopRequest() as stop:
            result = SortService(runtime, progress).execute(prepared, stop.requested)
    rest = (f'sort "{workbook}"' if workbook else "sort") if trial else None
    show_result(runtime, result, rest=rest)


def _confirm(runtime: Runtime, prepared: Prepared, *, yes: bool) -> bool:
    """Ask before sorting, unless `--yes` or `[sort] confirm = false`.

    Args:
        runtime: Settings, mount points and output.
        prepared: The sort.
        yes: `--yes` was given.

    Returns:
        True when the sort may proceed.

    """
    from media_hygiene.cli.fast_lines import tell_sort_twin
    from media_hygiene.cli.terminal import require_terminal

    if yes or not runtime.settings.sort.confirm:
        return True
    require_terminal(sys.stdin)
    tell_sort_twin(runtime)
    plan = prepared.plan
    return runtime.output.confirm(
        _("Move {count} files into {folders} folders?").format(
            count=len(plan.moves), folders=len(plan.folders)
        )
    )
