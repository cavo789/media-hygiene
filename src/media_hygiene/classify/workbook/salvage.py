"""Read the edits of any classify workbook, as far as they can be found: never refuse.

Unlike `sort`, which refuses a workbook whose structure changed, `classify` salvages
the edits of the previous workbook to carry them over: only the id column and the
editable columns are read, found by their header, rows matched by id in any order. A
value that cannot be used is set aside, never dropped silently.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.workbook.reader import open_book, read_meta
from media_hygiene.classify.workbook.salvage_cells import CellReader
from media_hygiene.classify.workbook.salvage_models import Words
from media_hygiene.classify.workbook.salvage_sheets import best_sheets
from media_hygiene.classify.workbook.sheets import Labels, MetaKey
from media_hygiene.errors import WorkbookError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.classify.workbook.salvage_cells import Table
    from media_hygiene.classify.workbook.salvage_models import Salvaged
    from media_hygiene.classify.workbook.salvage_sheets import Found, Kind


def salvage(path: Path) -> Salvaged:
    """Read every edit that can be found in a workbook.

    Args:
        path: The `.xlsx` file.

    Returns:
        The edits, keyed by the ids of the workbook's plan.

    Raises:
        WorkbookError: The file cannot be opened, or holds no sheet of a workbook.
    """
    book = open_book(path)
    try:
        try:
            meta = read_meta(book)
        except WorkbookError:
            meta = None
        sheets = [book[name] for name in book.sheetnames]
        tables: Table = [
            next(sheet.iter_rows(max_row=1, values_only=True), ()) for sheet in sheets
        ]
        chosen = best_sheets(tables)
        if not chosen:
            raise WorkbookError(
                _("{path}: no sheet of a classify workbook was found.").format(
                    path=path.name
                )
            )
        read: dict[Kind, tuple[Found, Table]] = {
            kind: (found, list(sheets[index].iter_rows(min_row=2, values_only=True)))
            for kind, (index, found) in chosen.items()
        }
    finally:
        book.close()
    words = Words.of(Labels.from_meta(meta) if meta else None)
    return CellReader(words).read(meta[MetaKey.PLAN_ID] if meta else "", read)
