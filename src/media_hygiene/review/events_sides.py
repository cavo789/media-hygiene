"""An event's value as the sort review page shows it: the workbook's, or the page's."""

from __future__ import annotations

from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.page_overlay import value_text

if TYPE_CHECKING:
    from media_hygiene.classify.page_values import EventValue


class Side(BaseModel):
    """A value as the page shows it: its text, and its parts to fill the fields."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    text: str = ""
    name: str = ""
    category: str = ""
    stay: bool = False


def event_side(value: EventValue) -> Side:
    """Show an event's value.

    Args:
        value: The workbook's or the page's.

    Returns:
        Its text and parts.
    """
    return Side(
        text=value_text(value),
        name=value.name,
        category=value.category,
        stay=value.stay,
    )
