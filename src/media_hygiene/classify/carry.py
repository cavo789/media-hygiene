"""Carry the human edits of the previous workbook over to a new plan.

A new `classify` (a setting changed, new photos) writes a new plan: the hours spent
naming events and moving files must not be lost. Files are matched by content, events
by the files they share, categories by name. An edit a sort already applied is not
carried: its files are in place. An edit that finds no target is listed, never dropped.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.carry_event_edits import carry_events
from media_hygiene.classify.carry_models import EditSheet, LostEdit, LostWhy
from media_hygiene.classify.carry_rows import row_map
from media_hygiene.classify.carry_types import Carried, typed_text
from media_hygiene.classify.workbook.edits import Edits
from media_hygiene.classify.workbook.salvage_models import Notes

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.carry_types import CarrySource
    from media_hygiene.classify.plan_file import ClassifyPlan


def carry_over(source: CarrySource, new: ClassifyPlan) -> Carried:
    """Match every edit of the previous workbook to the new plan.

    Args:
        source: The previous workbook.
        new: The new plan.

    Returns:
        What was carried over, and what was not.
    """
    return _Carrier(source, new).run()


class _Carrier:
    """Carries the edits of one workbook, listing those left behind."""

    def __init__(self, source: CarrySource, new: ClassifyPlan) -> None:
        """Match the rows of both plans.

        Args:
            source: The previous workbook.
            new: The new plan.
        """
        self._source, self._new = source, new
        self._rows = row_map(source.plan, new)
        old = source.plan.rows if source.plan else ()
        self._paths = {row.id: row.path for row in old}
        self._lost = list(source.salvaged.invalid)

    def run(self) -> Carried:
        """Carry the files, the events and the categories.

        Returns:
            What was carried over.
        """
        salvaged = self._source.salvaged
        files = self._files(salvaged.edits.files, applied=True)
        file_notes = self._files(salvaged.notes.files, applied=False)
        events = carry_events(self._source, self._new, self._rows)
        categories = self._categories(salvaged.edits.categories, applied=True)
        category_notes = self._categories(salvaged.notes.categories, applied=False)
        self._lost = [
            lost.model_copy(update={"key": self._paths.get(lost.key, lost.key)})
            if lost.sheet is EditSheet.FILES
            else lost
            for lost in self._lost
        ]
        return Carried(
            Edits(files, events.edits, categories),
            Notes(file_notes, events.notes, category_notes),
            events.split,
            (*self._lost, *events.lost),
        )

    def _files[T](self, edits: Mapping[str, T], *, applied: bool) -> dict[str, T]:
        """Carry the file edits (or notes) to the same content in the new plan.

        Args:
            edits: Previous row id → value.
            applied: Skip the rows a sort already moved (edits, not notes).

        Returns:
            New row id → value.
        """
        carried: dict[str, T] = {}
        for key, value in edits.items():
            if applied and key in self._source.applied:
                continue
            new_id = self._rows.get(key)
            if new_id is None:
                self._lose((EditSheet.FILES, key), value)
            else:
                carried[new_id] = value
        return carried

    def _categories[T](self, edits: Mapping[str, T], *, applied: bool) -> dict[str, T]:
        """Carry the category edits (or notes) by the proposed category name.

        Args:
            edits: Category → value.
            applied: Skip the categories whose files a sort all moved.

        Returns:
            Category → value, for the categories the new plan proposes.
        """
        proposed = self._new.categories()
        done = self._source.applied
        pending = {
            row.category
            for row in (self._source.plan.rows if self._source.plan else ())
            if row.id not in done
        }
        carried: dict[str, T] = {}
        for name, value in edits.items():
            if applied and done and name not in pending:
                continue
            if name in proposed:
                carried[name] = value
            else:
                self._lose((EditSheet.CATEGORIES, name), value)
        return carried

    def _lose(self, where: tuple[EditSheet, str], value: object) -> None:
        """List an edit that found no target: its file, event or category is gone.

        Args:
            where: The sheet it was typed on, and its file, event or category.
            value: What was typed.
        """
        sheet, key = where
        self._lost.append(
            LostEdit(sheet=sheet, key=key, value=typed_text(value), why=LostWhy.GONE)
        )
