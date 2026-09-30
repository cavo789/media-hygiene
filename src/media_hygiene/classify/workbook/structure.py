"""Check a workbook against its plan, all or nothing, before a single edit is read.

The sheets are rendered again from `plan.json`, in the language the workbook was written
in, and compared cell by cell: sheet names and order, header rows, the same row ids each
exactly once (matched by id, not by position), every locked cell. The first difference
refuses the whole file, naming its cell, what was expected and what was found.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.workbook.sheets import (
    META_SHEET,
    Labels,
    MetaKey,
    fingerprint,
)
from media_hygiene.classify.workbook.specs import locked_keys, sheet_specs
from media_hygiene.classify.workbook.structure_rows import (
    Place,
    difference,
    keyed,
    positional,
)
from media_hygiene.constants import Locale
from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _, using

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.rows import Row
    from media_hygiene.classify.workbook.sheet_edits import Table
    from media_hygiene.classify.workbook.specs import SheetSpec


@dataclass(frozen=True, slots=True)
class ReadBook:
    """What was read of a workbook: its sheet names, every row, its `_meta`."""

    names: tuple[str, ...]
    tables: Mapping[str, Table]  # visible sheet → its rows, headers first
    meta: Mapping[MetaKey, str]
    labels: Labels


def check_structure(book: ReadBook, plan: ClassifyPlan) -> None:
    """Refuse a workbook whose structure or locked cells differ from its plan.

    Args:
        book: What was read.
        plan: The plan the workbook was written for (same plan id).

    Raises:
        WorkbookError: The first difference, with the cell, expected and found values.
    """
    labels = book.labels
    expected = (labels.summary, labels.categories, labels.events, labels.files)
    if book.names != (*expected, META_SHEET):
        _refuse(
            _("The sheets were renamed, moved, added or deleted: {found}.").format(
                found=", ".join(name for name in book.names if name != META_SHEET)
            )
        )
    locale = language_of(labels)
    if locale is None:
        raise WorkbookError(
            _("This workbook was written by another version: it cannot be checked."),
            _("Run 'classify' again, then edit the new workbook."),
        )
    with using(locale):
        sheets = sheet_specs(plan, labels)
    if fingerprint(plan.plan_id, locked_keys(plan, sheets)) != book.meta.get(
        MetaKey.FINGERPRINT
    ):
        _refuse(_("The workbook and its plan.json do not match: one of them changed."))
    for spec, rows in sheets:
        different = _sheet_difference(spec, rows, book.tables[spec.title])
        if different is not None:
            _refuse(different)


def language_of(labels: Labels) -> Locale | None:
    """Tell the language a workbook was written in, from its sheet names and values.

    Args:
        labels: The labels its `_meta` recorded.

    Returns:
        The language, or None when no language of this version gives them.
    """
    for locale in Locale:
        with using(locale):
            if Labels.current() == labels:
                return locale
    return None


def _refuse(message: str) -> None:
    """Refuse the whole workbook.

    Args:
        message: What differs.

    Raises:
        WorkbookError: Always, with the tip to undo the change.
    """
    raise WorkbookError(message, undo_tip())


def undo_tip() -> str:
    """Tell how to repair a workbook whose structure changed.

    Returns:
        The translated tip.
    """
    return _("Undo the change in Excel (Ctrl+Z), or restore a copy of the workbook.")


def _sheet_difference(spec: SheetSpec, rows: list[Row], table: Table) -> str | None:
    """Compare one sheet with its rendering.

    Args:
        spec: The sheet, as written.
        rows: Its rows, as written.
        table: Its rows, as read, headers first.

    Returns:
        The first difference, or None.
    """
    found = table[0] if table else ()
    header = difference(spec.headers, found, Place(spec.title, 1))
    if header is not None:
        return header
    if not spec.filtered:  # the Summary: no ids, compared line by line
        return positional(spec, rows, table[1:])
    return keyed(spec, rows, table[1:])
