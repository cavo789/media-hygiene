"""The console side of `undo` of a sort run several times: which runs go back."""

from __future__ import annotations

from typing import TYPE_CHECKING

from rich.table import Table

from media_hygiene.classify.layout import month_name
from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from datetime import datetime

    from media_hygiene.actions.plan_runs import PlanRuns
    from media_hygiene.console.output import Output


def show_plan_runs(output: Output, plan: PlanRuns) -> None:
    """List the runs of the sort about to be undone, and why these ones.

    Args:
        output: The console.
        plan: The runs of the sort still to undo, newest first.
    """
    output.info(
        _(
            "Run {run_id} is part of a sort run several times with the same workbook: "
            "its runs are undone together, newest first."
        ).format(run_id=plan.named)
    )
    if plan.later is not None:
        output.info(
            _(
                "Run {later} of the same sort came after {run_id}: the undo starts "
                "from it, so that no later move stays on top."
            ).format(later=plan.later, run_id=plan.named)
        )
    for run_id in plan.undone:
        output.info(
            _("Run {run_id} of the same sort was already undone: left aside.").format(
                run_id=run_id
            )
        )
    table = Table(title=_("Runs to undo (newest first)"), title_justify="left")
    table.add_column(_("Run"), no_wrap=True)
    table.add_column(_("Started"))
    table.add_column(_("Files moved"), justify="right")
    for run in plan.runs:
        table.add_row(run.run_id, _when(run.started), human_number(run.moved))
    output.show(table)


def _when(moment: datetime) -> str:
    """Write a moment the way the console writes dates, in local time.

    Args:
        moment: A time-zone aware moment.

    Returns:
        Such as `30 September 2026 18:20`.
    """
    local = moment.astimezone()
    return _("{day} {month} {year} {time}").format(
        day=local.day,
        month=month_name(local.month),
        year=local.year,
        time=local.strftime("%H:%M"),
    )
