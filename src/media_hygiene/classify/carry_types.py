"""The previous workbook to carry over, and what was carried from it."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.workbook.edits import CategoryEdit, Stay
from media_hygiene.classify.workbook.sheets import Labels

if TYPE_CHECKING:
    from media_hygiene.classify.carry_models import LostEdit
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.edits import Edits
    from media_hygiene.classify.workbook.salvage_models import Notes, Salvaged


@dataclass(frozen=True, slots=True)
class CarrySource:
    """The previous workbook: what was salvaged, its plan, what a sort applied."""

    workbook: str  # host path, for the messages
    saved_at: str  # ISO date and time, local
    salvaged: Salvaged
    plan: ClassifyPlan | None  # None: its plan.json is gone
    applied: frozenset[str] = frozenset()  # previous rows a sort already moved


@dataclass(frozen=True, slots=True)
class Carried:
    """The edits and notes, keyed for the new plan, and those that found no target."""

    edits: Edits
    notes: Notes
    split: tuple[str, ...]  # the events whose edit went to several new events
    lost: tuple[LostEdit, ...]

    @property
    def count(self) -> int:
        """Count the edits carried over.

        Returns:
            Files, events and categories edited in the new plan.
        """
        edits = self.edits
        return len(edits.files) + len(edits.events) + len(edits.categories)

    @property
    def note_count(self) -> int:
        """Count the notes carried over.

        Returns:
            Them.
        """
        notes = self.notes
        return len(notes.files) + len(notes.events) + len(notes.categories)


def typed_text(value: object) -> str:
    """What was typed, as text.

    Args:
        value: A folder, "(stay where it is)", a note, a category edit.

    Returns:
        Its text.
    """
    if value is Stay.STAY:
        return Labels.current().stay
    if isinstance(value, CategoryEdit):
        return typed_text(value.rename) or Labels.current().yes
    return str(value)
