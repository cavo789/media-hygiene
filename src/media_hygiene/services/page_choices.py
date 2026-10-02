"""The choices of the review page of a plan: where they lie, and their conflicts.

They are saved in `sort-decisions.json`, in the folder of the `plan.json` they belong
to: the classify run's folder under `/reports`. `sort` and `classify` (carrying edits
over) both read them through here.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.classify.carry_models import EditSheet
from media_hygiene.classify.page_decisions import (
    PAGE_DECISIONS_FILE_NAME,
    read_page_decisions,
)
from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.page_decisions import PageDecisions
    from media_hygiene.classify.page_overlay import Conflict
    from media_hygiene.classify.plan_file import ClassifyPlan

_SHOWN: Final = 10


def page_file(plan_file: Path) -> Path:
    """The page's choices of a plan.

    Args:
        plan_file: Its `plan.json`.

    Returns:
        `sort-decisions.json` beside it (it may not exist).
    """
    return plan_file.with_name(PAGE_DECISIONS_FILE_NAME)


def page_decisions(plan_file: Path, plan: ClassifyPlan) -> PageDecisions:
    """Read the page's choices of a plan.

    Args:
        plan_file: Its `plan.json`.
        plan: The plan.

    Returns:
        The choices; none when the page was never used.
    """
    return read_page_decisions(page_file(plan_file), plan.plan_id)


def subject_of(plan: ClassifyPlan, conflict: Conflict) -> str:
    """Name the event or the file of a conflict as the user knows it.

    Args:
        plan: The plan.
        conflict: The conflict.

    Returns:
        `Event <name or dates> (<id>)`, or the host path of the file.
    """
    if conflict.sheet is EditSheet.FILES:
        rows = {row.id: row.path for row in plan.rows}
        return rows.get(conflict.key, conflict.key)
    events = {event.id: event.label or event.span for event in plan.events}
    title = events.get(conflict.key, "")
    return _("Event {name} ({id})").format(name=title, id=conflict.key)


def conflict_error(
    plan: ClassifyPlan, conflicts: tuple[Conflict, ...]
) -> WorkbookError:
    """Refuse a sort while the page and the workbook disagree on something.

    Args:
        plan: The plan.
        conflicts: Events and files chosen in the page, then edited otherwise in the
            workbook.

    Returns:
        The error, listing them.
    """
    message = ngettext(
        "{count} choice of the review page was edited otherwise in the workbook "
        "since; nothing was moved:",
        "{count} choices of the review page were edited otherwise in the workbook "
        "since; nothing was moved:",
        len(conflicts),
    ).format(count=len(conflicts))
    line = _("{subject}: page '{page}', workbook '{workbook}'")
    lines = [
        line.format(
            subject=subject_of(plan, conflict),
            page=conflict.page,
            workbook=conflict.workbook or _("(empty)"),
        )
        for conflict in conflicts[:_SHOWN]
    ]
    return WorkbookError(
        "\n".join((message, *lines)),
        _(
            "Choose again in 'review-sort' (it shows both), or set the workbook "
            "cells back, then run 'sort' again."
        ),
    )
