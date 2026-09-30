"""Compare the rows of a sheet with their rendering: by id, or line by line."""

from __future__ import annotations

import math
from dataclasses import dataclass
from typing import TYPE_CHECKING

from openpyxl.utils import get_column_letter

from media_hygiene.classify.workbook.sheet_edits import at
from media_hygiene.classify.workbook.validation import text_of
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.classify.workbook.rows import Row
    from media_hygiene.classify.workbook.sheet_edits import Table
    from media_hygiene.classify.workbook.specs import SheetSpec


@dataclass(frozen=True, slots=True)
class Place:
    """Where a row is, and the columns not compared (the editable ones)."""

    sheet: str
    number: int
    skip: frozenset[int] = frozenset()


def positional(spec: SheetSpec, rows: list[Row], table: Table) -> str | None:
    """Compare the rows of a sheet without ids (the Summary), line by line.

    Args:
        spec: The sheet.
        rows: Its rows, as written.
        table: Its rows, as read.

    Returns:
        The first difference, or None.
    """
    for index in range(max(len(rows), len(table))):
        want = rows[index] if index < len(rows) else ()
        got = table[index] if index < len(table) else ()
        place = Place(spec.title, index + 2, spec.editable)
        found = difference(want, got, place)
        if found is not None:
            return found
    return None


def keyed(spec: SheetSpec, rows: list[Row], table: Table) -> str | None:
    """Compare the rows of a sheet by their id (first column), each exactly once.

    Args:
        spec: The sheet.
        rows: Its rows, as written.
        table: Its rows, as read.

    Returns:
        The first difference, or None.
    """
    expected = {text_of(row[0]): row for row in rows}
    seen: set[str] = set()
    for number, got in enumerate(table, start=2):
        key = text_of(at(got, 1))
        if not key and not any(text_of(value) for value in got):
            continue
        cell = f"{spec.title}!A{number}"
        if key in seen:
            return _("{cell}: the row {key} appears twice.").format(cell=cell, key=key)
        if key not in expected:
            return _("{cell}: '{key}' is not a row of this plan.").format(
                cell=cell, key=key
            )
        seen.add(key)
        place = Place(spec.title, number, spec.editable)
        found = difference(expected[key], got, place)
        if found is not None:
            return found
    missing = next((key for key in expected if key not in seen), None)
    if missing is None:
        return None
    return _("{sheet}: the row {key} was deleted.").format(
        sheet=spec.title, key=missing
    )


def difference(want: Row, got: Sequence[object], place: Place) -> str | None:
    """Compare the locked cells of one row.

    Args:
        want: The row as written.
        got: The row as read.
        place: Where it is, and the columns not compared.

    Returns:
        The first locked cell that differs, or None.
    """
    for column in range(1, max(len(want), len(got)) + 1):
        if column in place.skip:
            continue
        expected, found = at(want, column), at(got, column)
        if not _same(expected, found):
            cell = f"{place.sheet}!{get_column_letter(column)}{place.number}"
            return _("{cell}: expected '{expected}', found '{found}'.").format(
                cell=cell, expected=text_of(expected), found=text_of(found)
            )
    return None


def _same(expected: object, found: object) -> bool:
    """Tell whether a locked cell kept its value: numbers within rounding.

    Args:
        expected: The value written.
        found: The value read.

    Returns:
        True when they are equal.
    """
    numbers = (int, float)
    if isinstance(expected, numbers) and isinstance(found, numbers):
        return math.isclose(expected, found, rel_tol=1e-9, abs_tol=1e-9)
    return text_of(expected) == text_of(found)
