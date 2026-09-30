"""The yellow cells a new workbook starts with: the edits carried over.

The edits stay where the user typed them, so that they can be changed again, and so
that the next `classify` carries them over again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.workbook.edits import Stay
from media_hygiene.classify.workbook.sheets import (
    CategoryColumn,
    EventColumn,
    FileColumn,
)

if TYPE_CHECKING:
    from media_hygiene.classify.workbook.edits import Choice, Edits
    from media_hygiene.classify.workbook.salvage_models import Notes
    from media_hygiene.classify.workbook.sheets import Labels

type Cells = dict[str, dict[str, dict[int, str]]]  # sheet → key → column → text


@dataclass(frozen=True, slots=True)
class Prefill:
    """The edits and notes to write in the yellow cells, keyed for the plan."""

    edits: Edits
    notes: Notes

    def cells(self, labels: Labels) -> Cells:
        """The texts of the yellow cells.

        Args:
            labels: The sheet names and drop-down values written.

        Returns:
            Sheet title → row key → column → text.
        """
        edits, notes = self.edits, self.notes
        files: dict[str, dict[int, str]] = {
            key: {FileColumn.FINAL: _text(choice, labels)}
            for key, choice in edits.files.items()
        }
        events: dict[str, dict[int, str]] = {
            key: {
                EventColumn.NAME: edit.name,
                EventColumn.CATEGORY: _text(edit.category, labels),
            }
            for key, edit in edits.events.items()
        }
        categories: dict[str, dict[int, str]] = {
            key: {
                CategoryColumn.RENAME: _text(edit.rename, labels),
                CategoryColumn.CONFIRM: labels.yes if edit.confirm else "",
            }
            for key, edit in edits.categories.items()
        }
        for table, column, typed in (
            (files, FileColumn.NOTES, notes.files),
            (events, EventColumn.NOTES, notes.events),
            (categories, CategoryColumn.NOTES, notes.categories),
        ):
            for key, note in typed.items():
                table.setdefault(key, {})[column] = note
        return {
            labels.files: files,
            labels.events: events,
            labels.categories: categories,
        }


def _text(choice: Choice, labels: Labels) -> str:
    """A drop-down value as the workbook writes it.

    Args:
        choice: A folder, "(stay where it is)", or empty.
        labels: The drop-down values written.

    Returns:
        Its text.
    """
    return labels.stay if choice is Stay.STAY else choice
