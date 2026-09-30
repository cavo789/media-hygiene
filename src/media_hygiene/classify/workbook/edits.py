"""What the user changed in the workbook, and the folder it gives each file.

Precedence: file > event > category. A human edit counts as sure: the file leaves the
"to check" band. Files left as they are (protected, `leave`) ignore every edit. Each
decision says where it comes from, so that `sort` can let a file edit on any companion
(a Live Photo's video, a RAW twin) decide for the whole group.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from enum import Enum, IntEnum
from typing import TYPE_CHECKING

from media_hygiene.classify.layout import render
from media_hygiene.classify.models import Band

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow


class Stay(Enum):
    """The "(stay where it is)" value of the drop-downs."""

    STAY = "stay"


type Choice = str | Stay


class Source(IntEnum):
    """Where a decision comes from; a lower value wins among companions."""

    FILE = 0  # a cell of the Files sheet
    GROUP = 1  # an edit of its event or of its category
    PROPOSAL = 2  # nothing edited: what classify proposed


@dataclass(frozen=True, slots=True)
class EventEdit:
    """The name and the category the user gave an event; empty: unchanged."""

    name: str = ""
    category: Choice = ""


@dataclass(frozen=True, slots=True)
class CategoryEdit:
    """A category renamed (or left in place), its "to check" files confirmed."""

    rename: Choice = ""
    confirm: bool = False


@dataclass(frozen=True, slots=True)
class Edits:
    """Every editable cell the user filled, by row id, event id and category."""

    files: Mapping[str, Choice] = field(default_factory=dict)
    events: Mapping[str, EventEdit] = field(default_factory=dict)
    categories: Mapping[str, CategoryEdit] = field(default_factory=dict)
    file_cells: Mapping[str, str] = field(default_factory=dict)  # row id → "Files!K7"


@dataclass(frozen=True, slots=True)
class Decision:
    """Where one file goes once the edits are applied."""

    row: PlanRow
    folder: str | None  # relative to the row's root; None: stays where it is
    band: Band  # SURE after a human edit
    source: Source = Source.PROPOSAL
    cell: str = ""  # the Files sheet cell of a file edit, for the messages


def resolve(plan: ClassifyPlan, edits: Edits) -> tuple[Decision, ...]:
    """Apply the edits to every row of the plan.

    Args:
        plan: The plan.
        edits: What the user changed.

    Returns:
        One decision per row, in the plan's order.
    """
    return tuple(_decide(row, plan, edits) for row in plan.rows)


def _decide(row: PlanRow, plan: ClassifyPlan, edits: Edits) -> Decision:
    """The folder of one row: its file edit, else its event's, else its category's.

    Args:
        row: A row.
        plan: The plan (its layouts).
        edits: What the user changed.

    Returns:
        Its decision.
    """
    unchanged = Decision(row, row.folder, row.band)
    if row.band is Band.STAY or row.values is None:
        return unchanged
    if row.id in edits.files:
        choice = edits.files[row.id]
        folder = None if choice is Stay.STAY else choice
        cell = edits.file_cells.get(row.id, "")
        return Decision(row, folder, Band.SURE, Source.FILE, cell)
    event = edits.events.get(row.event_id)
    if event is not None and (event.name or event.category):
        return _by_event(row, event, (plan, edits))
    category = edits.categories.get(row.category)
    decided = None if category is None else _by_category(row, category, plan)
    return unchanged if decided is None else replace(decided, source=Source.GROUP)


def _by_event(
    row: PlanRow, event: EventEdit, context: tuple[ClassifyPlan, Edits]
) -> Decision:
    """The folder an event edit gives: its name is the category when none is given.

    Args:
        row: A row of the event.
        event: The edit of its event.
        context: The plan and every edit (a renamed category applies too).

    Returns:
        Its decision, sure.
    """
    plan, edits = context
    if event.category is Stay.STAY or row.values is None:
        return Decision(row, None, Band.SURE, Source.GROUP)
    renamed = edits.categories.get(row.category)
    current = renamed.rename if renamed and isinstance(renamed.rename, str) else ""
    category = event.category or event.name or current or row.category
    values = replace(
        row.values.as_values(), category=category, event=event.name or row.values.event
    )
    return Decision(row, render(plan.layout, values), Band.SURE, Source.GROUP)


def _by_category(
    row: PlanRow, edit: CategoryEdit, plan: ClassifyPlan
) -> Decision | None:
    """The folder a category edit gives, to its sure and confirmed files.

    Args:
        row: A row of the category.
        edit: The edit of its category.
        plan: The plan (its layouts).

    Returns:
        Its decision, or None when the edit does not concern this row.
    """
    if edit.rename is Stay.STAY:
        return Decision(row, None, Band.SURE)
    if row.values is None:
        return None
    confirmed = row.band is Band.UNSURE and edit.confirm
    if row.band is not Band.SURE and not confirmed:
        if not edit.rename or row.band is not Band.UNSURE:
            return None
        values = replace(row.values.as_values(), category=edit.rename)
        return Decision(row, render(plan.unsure_layout, values), row.band)
    values = replace(row.values.as_values(), category=edit.rename or row.category)
    return Decision(row, render(plan.layout, values), Band.SURE)
