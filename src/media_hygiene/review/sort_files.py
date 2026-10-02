"""Photos sent out of their event in the sort review: checked, then written down.

A photo sent to another category gets the folder the sure layout gives it with that
category, as if its row of the Files sheet had been typed: a human choice is sure.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.layout import render
from media_hygiene.classify.models import Band
from media_hygiene.classify.page_decisions import FileDecision
from media_hygiene.classify.page_values import FileValue
from media_hygiene.classify.workbook.validation import folder_problem
from media_hygiene.errors import DecisionsError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.classify.worklist import WorkItem
    from media_hygiene.paths.host_paths import HostPathMapper


@dataclass(frozen=True, slots=True)
class SortSource:
    """What a sort review is about: the plan, the workbook's edits, where to save."""

    plan: ClassifyPlan
    workbook: Edits  # as read when the review started
    target: Path  # `sort-decisions.json`, in the container
    hosts: tuple[str, str]  # the workbook and the decisions file, on the host
    mapper: HostPathMapper


@dataclass(frozen=True, slots=True)
class SendFiles:
    """Photos of an event sent to another category, or left where they are."""

    event: str
    rows: tuple[str, ...]
    category: str = ""
    stay: bool = False


def movable_rows(item: WorkItem, request: SendFiles) -> list[PlanRow]:
    """The photos of a request, checked.

    Args:
        item: Their event.
        request: The photos and where they go.

    Returns:
        Their rows.

    Raises:
        DecisionsError: A photo of another event, one left as it is, or a category
            that cannot be a folder.
    """
    members = {row.id: row for row in item.rows}
    if not request.rows or any(row not in members for row in request.rows):
        raise DecisionsError(_("Choose photos of this event."))
    if not (request.category or request.stay):
        raise DecisionsError(_("Type a category, or leave the photos in place."))
    problem = None if request.stay else folder_problem(request.category)
    if problem is not None:
        raise DecisionsError(problem)
    rows = [members[row] for row in request.rows]
    fixed = [row for row in rows if row.values is None or row.band is Band.STAY]
    if fixed:
        message = _("{path} is left as it is: no choice applies to it.")
        raise DecisionsError(message.format(path=fixed[0].path))
    return rows


def file_decisions(
    source: SortSource, rows: list[PlanRow], request: SendFiles
) -> list[FileDecision]:
    """Write down where each photo goes, and what the workbook said of it.

    Args:
        source: The plan (its sure layout) and the workbook's edits.
        rows: The photos, checked by `movable_rows`.
        request: Where they go.

    Returns:
        One decision per photo.
    """
    decisions: list[FileDecision] = []
    for row in rows:
        folder = None
        if not request.stay and row.values is not None:
            values = replace(row.values.as_values(), category=request.category)
            folder = render(source.plan.layout, values)
        decisions.append(
            FileDecision(
                row=row.id,
                value=FileValue(folder=folder or "", stay=folder is None),
                base=FileValue.of(source.workbook.files.get(row.id)),
                category="" if request.stay else request.category,
            )
        )
    return decisions
