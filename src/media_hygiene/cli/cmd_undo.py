"""`media-hygiene undo`: restore the files of a run (clean, or every run of a sort)."""

from __future__ import annotations

import sys
from typing import TYPE_CHECKING, Annotated

import typer

from media_hygiene.cli.context import runtime_of, user_errors
from media_hygiene.cli.flows import require_terminal
from media_hygiene.console.formatting import human_number
from media_hygiene.console.progress import RichProgress
from media_hygiene.console.tables import outcome_table
from media_hygiene.console.undo_view import show_plan_runs
from media_hygiene.constants import ExitCode
from media_hygiene.i18n import _, ngettext
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.clean import CleanService
from media_hygiene.services.undo import (
    resolve_run_id,
    run_kind,
    runs_to_undo,
    undo_runs,
)

if TYPE_CHECKING:
    from media_hygiene.actions.plan_runs import PlanRuns
    from media_hygiene.services.runtime import Runtime


def undo_command(
    ctx: typer.Context,
    run_id: Annotated[
        str | None,
        typer.Argument(
            help=_(
                "Run to undo (see 'history'); the latest one by default. For a sort, "
                "every run of the same workbook."
            )
        ),
    ] = None,
    *,
    yes: Annotated[
        bool,
        typer.Option(
            "--yes",
            "-y",
            help=_(
                "Do not ask for confirmation before undoing several runs of a sort "
                "(overrides sort.confirm)."
            ),
        ),
    ] = False,
) -> None:
    """Restore every file a run deleted, quarantined or moved.

    Args:
        ctx: Typer context holding the runtime.
        run_id: Run identifier, or None for the latest run.
        yes: `--yes`, skip the confirmation.

    Raises:
        typer.Exit: The user declined.
    """
    runtime = runtime_of(ctx)
    output = runtime.output
    with user_errors(output):
        run = resolve_run_id(runtime, run_id)
        CleanService(runtime, NullProgress()).ensure_ready()
        plan = runs_to_undo(runtime, run)
        title = _title(runtime, run, plan)
        output.title(title)
        if plan is not None and plan.together:
            show_plan_runs(output, plan)
            if not _confirm(runtime, plan, yes=yes):
                output.info(_("Nothing was changed."))
                raise typer.Exit(ExitCode.OK)
        runs = [run] if plan is None else [each.run_id for each in plan.runs]
        with RichProgress(output.console) as progress:
            outcome = undo_runs(runtime, runs, progress)
    output.show(outcome_table(outcome, title))
    for incident in outcome.skipped:
        output.warning(f"{runtime.mapper.to_host(incident.path)}: {incident.reason}")
    for incident in outcome.failed:
        output.error(f"{runtime.mapper.to_host(incident.path)}: {incident.reason}")


def _title(runtime: Runtime, run: str, plan: PlanRuns | None) -> str:
    """Name what is undone: one run, or the runs of one sort.

    Args:
        runtime: Settings, mount points and output.
        run: The run named.
        plan: The runs of the sort, or None for a clean run.

    Returns:
        The translated title.
    """
    if plan is not None and plan.together:
        count = len(plan.runs)
        return ngettext(
            "Undo the {count} run left of the sort",
            "Undo the {count} runs of the sort",
            count,
        ).format(count=count)
    return _("Undo the {command} run {run_id}").format(
        command=run_kind(runtime, run).value, run_id=run
    )


def _confirm(runtime: Runtime, plan: PlanRuns, *, yes: bool) -> bool:
    """Ask before undoing several runs, unless `--yes` or `[sort] confirm = false`.

    Args:
        runtime: Settings, mount points and output.
        plan: The runs about to be undone.
        yes: `--yes` was given.

    Returns:
        True when the undo may proceed.
    """
    if yes or not runtime.settings.sort.confirm:
        return True
    require_terminal(sys.stdin)
    count = len(plan.runs)
    question = ngettext(
        "Undo this run and move {moved} files back?",
        "Undo these {count} runs and move {moved} files back?",
        count,
    )
    moved = sum(run.moved for run in plan.runs)
    return runtime.output.confirm(
        question.format(count=count, moved=human_number(moved))
    )
