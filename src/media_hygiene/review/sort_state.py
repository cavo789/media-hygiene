"""The answers of the sort review: the whole state, one event, the categories used."""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.review.sort_views import EventCard, PhotoCard

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.classify.page_decisions import EventDecision
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.edits import Edits

_FROZEN = ConfigDict(frozen=True, extra="forbid")


class SortState(BaseModel):
    """Everything the page needs at first: `GET /api/state`."""

    model_config = _FROZEN

    workbook: str  # host path
    decisions: str  # host path of `sort-decisions.json`
    categories: tuple[str, ...]  # for the completion, the most used first
    events: tuple[EventCard, ...]


class EventView(BaseModel):
    """One event and its photos: `GET /api/event/<id>`, and every choice's answer."""

    model_config = _FROZEN

    card: EventCard
    photos: tuple[PhotoCard, ...]


def categories_used(
    plan: ClassifyPlan, workbook: Edits, chosen: Iterable[EventDecision]
) -> tuple[str, ...]:
    """The categories to complete from: proposed, typed in the workbook or the page.

    Args:
        plan: The plan.
        workbook: The workbook's edits.
        chosen: The page's event choices.

    Returns:
        Them, the most used first.
    """
    used = Counter(plan.categories())
    typed = [edit.category or edit.name for edit in workbook.events.values()]
    typed += [item.value.category or item.value.name for item in chosen]
    used.update(text for text in typed if isinstance(text, str) and text)
    return tuple(name for name, _count in used.most_common())
