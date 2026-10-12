"""The one step `status` ends with, as a full command, and how to undo the last run."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.cli.next_steps import carried, safety, suggest
from media_hygiene.cli.review_options import PAGE_PORT
from media_hygiene.cli.status_view import days_since
from media_hygiene.constants import RunKind
from media_hygiene.i18n import _
from media_hygiene.review.place import DEFAULT_DECISIONS, decisions_flag
from media_hygiene.services.next_command import CHANGING, NextVerb

if TYPE_CHECKING:
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.status import Status


def advise_status(runtime: Runtime, status: Status) -> None:
    """Add the undo line of the newest run, then the one step that comes next.

    Args:
        runtime: Settings, mount points and output.
        status: What the tool folders say.
    """
    if status.undoable:
        run_id = status.undoable[0].run_id
        safety(
            runtime,
            _("'undo {run_id}' still restores the files of the last run:").format(
                run_id=run_id
            ),
            NextVerb(carried(runtime, f"undo {run_id}"), CHANGING),
        )
    step = _next_step(runtime, status)
    if step is None:
        runtime.output.success(_("Nothing left to do: everything is applied."))
        return
    text, verb = step
    suggest(runtime, text, verb)


def _next_step(runtime: Runtime, status: Status) -> tuple[str, NextVerb] | None:
    """Choose the step: the first thing left, in the order of the guide.

    Args:
        runtime: Settings, mount points and output.
        status: What the tool folders say.

    Returns:
        The text and the command, or None when nothing is left.
    """
    summary, review = status.analysis.summary, status.review
    if status.blank:
        return _("start with an audit: it changes nothing."), NextVerb(
            carried(runtime, "audit")
        )
    if summary and summary.kind is RunKind.AUDIT and summary.duplicate_files:
        return _("the last audit found extra copies: 'clean' sets them aside."), (
            NextVerb(carried(runtime, "clean"), CHANGING)
        )
    if review.bursts_to_see:
        return _("finish the burst review where you stopped."), NextVerb(
            carried(runtime, "review"), port=PAGE_PORT
        )
    if review.shots_set_aside or review.near_groups:
        tier = "--tier near " if review.near_groups else ""
        command = f"clean {tier}{decisions_flag(DEFAULT_DECISIONS)}"
        return _("apply your review: the files you set aside go to the quarantine."), (
            NextVerb(carried(runtime, command), CHANGING)
        )
    return _quarantine_or_sort(runtime, status)


def _quarantine_or_sort(
    runtime: Runtime, status: Status
) -> tuple[str, NextVerb] | None:
    """An old quarantine first, then a proposal not sorted, then a recent quarantine.

    Args:
        runtime: Settings, mount points and output.
        status: What the tool folders say.

    Returns:
        The text and the command, or None when nothing is left.
    """
    runs = status.quarantine.runs
    hint = runtime.settings.clean.purge_hint_days
    old = [run for run in runs if days_since(run.started) >= hint]
    if old:
        run_id = old[-1].run_id
        text = _(
            "the quarantine of {run_id} is more than {days} days old: once checked, "
            "'purge' frees its space."
        ).format(run_id=run_id, days=hint)
        return text, NextVerb(carried(runtime, f"purge {run_id}"), CHANGING)
    if status.sort.proposed is not None and not status.sort.sorted:
        return _("the classify proposal waits: 'sort' applies the edited workbook."), (
            NextVerb(carried(runtime, "sort"), CHANGING)
        )
    if runs:
        run_id = runs[0].run_id
        return _(
            "once you have checked the quarantine, 'purge' frees its space."
        ), NextVerb(carried(runtime, f"purge {run_id}"), CHANGING)
    return None
