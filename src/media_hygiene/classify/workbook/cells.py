"""The cells and sheets of a write-only workbook: locked, bold, or editable.

openpyxl stores any text starting with `=` as a formula: a file named `=1.jpg` would
make Excel report a damaged workbook. Every cell is made through `text_safe_cell`,
which keeps such text as text.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Protocol

from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill, Protection

if TYPE_CHECKING:
    from collections.abc import Iterable
    from datetime import datetime

    from openpyxl.cell.cell import Cell
    from openpyxl.worksheet._write_only import WriteOnlyWorksheet
    from openpyxl.worksheet.datavalidation import DataValidationList
    from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
    from openpyxl.worksheet.filters import AutoFilter
    from openpyxl.worksheet.protection import SheetProtection

_TEXT: Final = "@"
_FORMULA: Final = "="
_STRING: Final = "s"
_EDITABLE_FILL: Final = PatternFill("solid", start_color="FFF2CC")
_BOLD: Final = Font(bold=True)
_UNLOCKED: Final = Protection(locked=False)

type Value = str | int | float | None


class WriteOnly(Protocol):
    """What a write-only sheet has at runtime, and its type stubs omit."""

    protection: SheetProtection
    column_dimensions: DimensionHolder[str, ColumnDimension]
    sheet_state: str
    data_validations: DataValidationList
    auto_filter: AutoFilter
    freeze_panes: str | None

    def append(self, row: Iterable[Cell | Value]) -> None:
        """Add a row.

        Args:
            row: Its cells.
        """


def text_safe_cell(sheet: WriteOnlyWorksheet, value: Value | datetime) -> Cell:
    """A cell whose text is always text, never a formula.

    Args:
        sheet: Its sheet.
        value: Its value.

    Returns:
        The cell.
    """
    written = WriteOnlyCell(sheet, value=value)
    if isinstance(value, str) and value.startswith(_FORMULA):
        written.data_type = _STRING  # a name such as "=1.jpg" is text, not a formula
    return written


def header_cell(sheet: WriteOnlyWorksheet, value: Value) -> Cell:
    """A locked, bold cell.

    Args:
        sheet: Its sheet.
        value: Its value.

    Returns:
        The cell.
    """
    written = text_safe_cell(sheet, value)
    written.font = _BOLD
    return written


def locked_cell(
    sheet: WriteOnlyWorksheet, value: Value, number_format: str | None
) -> Cell:
    """A locked cell.

    Args:
        sheet: Its sheet.
        value: Its value.
        number_format: Its number format, if any.

    Returns:
        The cell.
    """
    written = text_safe_cell(sheet, value)
    if number_format is not None:
        written.number_format = number_format
    return written


def editable_cell(sheet: WriteOnlyWorksheet, value: Value) -> Cell:
    """An unlocked, yellow cell in the Text format.

    Args:
        sheet: Its sheet.
        value: Its value.

    Returns:
        The cell.
    """
    written = text_safe_cell(sheet, value)
    written.protection = _UNLOCKED
    written.number_format = _TEXT
    written.fill = _EDITABLE_FILL
    return written


def padded(row: tuple[Value, ...], size: int) -> tuple[Value, ...]:
    """A row with its editable cells, even past its last value.

    Args:
        row: The values.
        size: The sheet's last editable column.

    Returns:
        The row, at least `size` long.
    """
    return (*row, *([None] * (size - len(row))))
