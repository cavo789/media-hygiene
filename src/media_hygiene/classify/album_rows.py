"""Which rows of a classify plan an album gathers: by category, event or rule.

The plan is read with the user's edits: a category renamed in the workbook, or an event
named, is the one the album asks for, as `sort` would apply it. Every criterion given
must match (`--category Noël --rule Christmas`: both); none given gathers nothing.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanEvent, PlanRow
    from media_hygiene.classify.workbook.edits import Edits


@dataclass(frozen=True, slots=True)
class Criteria:
    """What an album gathers; empty values are not asked for."""

    category: str = ""
    event: str = ""  # an event id, or its name
    rule: str = ""  # the name of a `[[classify.rules]]` entry
    rating: int = 0  # at least these Windows stars (1 to 5); 0: not asked

    @property
    def given(self) -> bool:
        """Tell whether anything is asked for.

        Returns:
            True when at least one criterion is set.
        """
        return bool(self.category or self.event or self.rule or self.rating)


@dataclass(frozen=True, slots=True)
class _Context:
    """The plan's events by id, and the user's edits."""

    events: Mapping[str, PlanEvent]
    edits: Edits


def chosen_rows(
    plan: ClassifyPlan, edits: Edits, criteria: Criteria
) -> tuple[PlanRow, ...]:
    """List the rows matching the category, event and rule asked for.

    The rating is not known to the plan: the caller checks it in the index.

    Args:
        plan: The classify plan.
        edits: What the user changed in the workbook and the review page.
        criteria: What the album gathers.

    Returns:
        The matching rows, in the plan's order.
    """
    context = _Context({event.id: event for event in plan.events}, edits)
    return tuple(row for row in plan.rows if _matches(row, context, criteria))


def _matches(row: PlanRow, context: _Context, criteria: Criteria) -> bool:
    """Tell whether a row matches every criterion given (the rating apart).

    Args:
        row: A row.
        context: The events and the edits.
        criteria: What the album gathers.

    Returns:
        True when it does.
    """
    category = category_of(row, context.edits)
    if criteria.category and not _same(category, criteria.category):
        return False
    if criteria.rule and not _same(row.rule, criteria.rule):
        return False
    if not criteria.event:
        return True
    event = context.events.get(row.event_id)
    if event is None:
        return False
    names = (event.id, event_name(event, context.edits))
    return any(_same(name, criteria.event) for name in names)


def category_of(row: PlanRow, edits: Edits) -> str:
    """The category of a row once edited, as `sort` decides it.

    An event named (or given a category) gives its rows its category, else its name;
    a renamed category gives its new name.

    Args:
        row: A row.
        edits: What the user changed.

    Returns:
        The category; empty for a file left where it is.
    """
    if row.values is None:
        return ""
    renamed = edits.categories.get(row.category)
    current = row.category
    if renamed is not None and isinstance(renamed.rename, str) and renamed.rename:
        current = renamed.rename
    event = edits.events.get(row.event_id)
    if event is None:
        return current
    chosen = event.category if isinstance(event.category, str) else ""
    return chosen or event.name or current


def event_name(event: PlanEvent, edits: Edits) -> str:
    """The name of an event: given by the user, else its folder's, else its dates.

    Args:
        event: An event.
        edits: What the user changed.

    Returns:
        Its name.
    """
    edit = edits.events.get(event.id)
    return (edit.name if edit else "") or event.label or event.span


def _same(value: str, asked: str) -> bool:
    """Compare two names the way a user means them: case and spaces ignored.

    Args:
        value: A name in the plan.
        asked: The name typed.

    Returns:
        True when they are the same name.
    """
    return value.strip().casefold() == asked.strip().casefold()
