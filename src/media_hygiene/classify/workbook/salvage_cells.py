"""The cells salvaged from a workbook: edits and notes by key, unusable values aside."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.carry_models import EditSheet, LostEdit, LostWhy
from media_hygiene.classify.workbook.edits import CategoryEdit, Edits, EventEdit, Stay
from media_hygiene.classify.workbook.salvage_models import Notes, Salvaged
from media_hygiene.classify.workbook.salvage_sheets import Kind, Role
from media_hygiene.classify.workbook.validation import (
    folder_of,
    folder_problem,
    text_of,
)

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.classify.workbook.edits import Choice
    from media_hygiene.classify.workbook.salvage_models import Words
    from media_hygiene.classify.workbook.salvage_sheets import Found

type Table = list[Sequence[object]]


class CellReader:
    """Reads the cells of the sheets found, setting aside the values unusable."""

    def __init__(self, words: Words) -> None:
        """Start with nothing set aside.

        Args:
            words: The drop-down values.
        """
        self._words = words
        self._invalid: list[LostEdit] = []

    def read(self, plan_id: str, read: Mapping[Kind, tuple[Found, Table]]) -> Salvaged:
        """Read the edits and notes of every sheet found.

        Args:
            plan_id: The plan id `_meta` recorded, or empty.
            read: Each sheet found: its columns and its rows below the header.

        Returns:
            What was salvaged.
        """
        by_kind = {kind: cells(found, table) for kind, (found, table) in read.items()}
        files = by_kind.get(Kind.FILES, [])
        events = by_kind.get(Kind.EVENTS, [])
        categories = by_kind.get(Kind.CATEGORIES, [])
        edits = Edits(
            files={
                key: choice
                for key, row in files
                if (choice := self._choice(row, (Role.FINAL, EditSheet.FILES, key)))
            },
            events=self._events(events),
            categories=self._categories(categories),
        )
        notes = Notes(
            *(
                {key: row[Role.NOTES] for key, row in rows if row.get(Role.NOTES)}
                for rows in (files, events, categories)
            )
        )
        return Salvaged(plan_id, edits, notes, tuple(self._invalid))

    def _choice(
        self, row: Mapping[Role, str], where: tuple[Role, EditSheet, str]
    ) -> Choice:
        """A folder or "(stay where it is)"; an unusable folder is set aside.

        Args:
            row: The texts of a row, by role.
            where: The column, the sheet and the key, for what is set aside.

        Returns:
            The value; empty when there is none or it cannot be used.
        """
        role, sheet, key = where
        text = row.get(role, "")
        if not text:
            return ""
        if text in self._words.stay:
            return Stay.STAY
        if folder_problem(text) is not None:
            self._invalid.append(
                LostEdit(sheet=sheet, key=key, value=text, why=LostWhy.INVALID)
            )
            return ""
        return folder_of(text)

    def _events(self, rows: list[tuple[str, dict[Role, str]]]) -> dict[str, EventEdit]:
        """The names and categories of the Events sheet.

        Args:
            rows: Its rows: id and texts.

        Returns:
            Event id → its edit.
        """
        edits: dict[str, EventEdit] = {}
        for key, row in rows:
            name = self._choice(row, (Role.NAME, EditSheet.EVENTS, key))
            category = self._choice(row, (Role.CATEGORY, EditSheet.EVENTS, key))
            text = name if isinstance(name, str) else ""
            if text or category:
                edits[key] = EventEdit(text, category)
        return edits

    def _categories(
        self, rows: list[tuple[str, dict[Role, str]]]
    ) -> dict[str, CategoryEdit]:
        """The new names and confirmations of the Categories sheet.

        Args:
            rows: Its rows: category and texts.

        Returns:
            Category → its edit.
        """
        edits: dict[str, CategoryEdit] = {}
        words = self._words
        for key, row in rows:
            rename = self._choice(row, (Role.RENAME, EditSheet.CATEGORIES, key))
            confirm = row.get(Role.CONFIRM, "")
            if confirm and confirm not in words.yes | words.no:
                self._invalid.append(
                    LostEdit(
                        sheet=EditSheet.CATEGORIES,
                        key=key,
                        value=confirm,
                        why=LostWhy.INVALID,
                    )
                )
            if rename or confirm in words.yes:
                edits[key] = CategoryEdit(rename, confirm in words.yes)
        return edits


def cells(found: Found, table: Table) -> list[tuple[str, dict[Role, str]]]:
    """The texts of the columns found, for every row with a key.

    Args:
        found: The sheet's columns.
        table: Its rows below the header.

    Returns:
        Key and texts by role, in the sheet's order.
    """
    keyed: list[tuple[str, dict[Role, str]]] = []
    for row in table:
        texts = {
            role: text_of(row[column]) if column < len(row) else ""
            for role, column in found.columns.items()
        }
        key = texts.pop(Role.KEY)
        if key:
            keyed.append((key, texts))
    return keyed
