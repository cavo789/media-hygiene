"""The cells and sheets of a write-only workbook: locked, bold, or editable."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, Protocol

from openpyxl.cell import WriteOnlyCell
from openpyxl.styles import Font, PatternFill, Protection

if TYPE_CHECKING:
    from collections.abc import Iterable

    from openpyxl.cell.cell import Cell
    from openpyxl.worksheet._write_only import WriteOnlyWorksheet
    from openpyxl.worksheet.datavalidation import DataValidationList
    from openpyxl.worksheet.dimensions import ColumnDimension, DimensionHolder
    from openpyxl.worksheet.filters import AutoFilter
    from openpyxl.worksheet.protection import SheetProtection

_TEXT: Final = "@"
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


def header_cell(sheet: WriteOnlyWorksheet, value: Value) -> Cell:
    """A locked, bold cell.

    Args:
        sheet: Its sheet.
        value: Its value.

    Returns:
        The cell.
    """
    written = WriteOnlyCell(sheet, value=value)
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
    written = WriteOnlyCell(sheet, value=value)
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
    written = WriteOnlyCell(sheet, value=value)
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
