"""The sheets of the classify workbook: their headers, rows and editable columns.

The writer lays them out; the reader renders them again to check, cell by cell, that
nothing locked was changed.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.workbook import rows as content
from media_hygiene.classify.workbook.sheets import (
    META_LIST_COLUMN,
    META_SHEET,
    CategoryColumn,
    EventColumn,
    FileColumn,
)
from media_hygiene.classify.workbook.summary import summary_headers, summary_rows

if TYPE_CHECKING:
    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.classify.workbook.rows import Row
    from media_hygiene.classify.workbook.sheets import Labels

_PERCENT: Final = "0%"
_WIDE: Final = 40
_SUMMARY_WIDTHS: Final = (60, 24, _WIDE)
_SUMMARY_NOTES: Final = 3


@dataclass(frozen=True, slots=True)
class SheetSpec:
    """One protected sheet: its headers, its editable columns, its drop-downs."""

    title: str
    headers: Row
    editable: frozenset[int]
    lists: dict[int, str] = field(default_factory=dict)  # column → list formula
    formats: dict[int, str] = field(default_factory=dict)  # column → number format
    widths: tuple[int, ...] = ()  # the first columns' widths; the others: _WIDTH
    filtered: bool = True  # an auto-filter on the header row

    @property
    def width(self) -> int:
        """The last column the sheet writes.

        Returns:
            Its number, 1-based.
        """
        return max(len(self.headers), *self.editable)


type Sheets = list[tuple[SheetSpec, list[Row]]]


def sheet_specs(plan: ClassifyPlan, labels: Labels) -> Sheets:
    """The four visible sheets and their rows, in the workbook's order.

    Args:
        plan: The plan.
        labels: The translated names and values.

    Returns:
        Each sheet with its rows.
    """
    last = len(plan.categories()) + 1
    choices = f"'{META_SHEET}'!${META_LIST_COLUMN}$1:${META_LIST_COLUMN}${last}"
    category = CategoryColumn
    event = EventColumn
    return [
        (
            SheetSpec(
                labels.summary,
                summary_headers(labels),
                frozenset({_SUMMARY_NOTES}),
                widths=_SUMMARY_WIDTHS,
                filtered=False,
            ),
            summary_rows(plan),
        ),
        (
            SheetSpec(
                labels.categories,
                content.category_headers(),
                frozenset({category.RENAME, category.CONFIRM, category.NOTES}),
                {
                    category.RENAME: choices,
                    category.CONFIRM: f'"{labels.yes},{labels.no}"',
                },
            ),
            content.category_rows(plan),
        ),
        (
            SheetSpec(
                labels.events,
                content.event_headers(),
                frozenset({event.NAME, event.CATEGORY, event.NOTES}),
                {event.CATEGORY: choices},
                {event.SHARE: _PERCENT},
            ),
            content.event_rows(plan, labels),
        ),
        (
            SheetSpec(
                labels.files,
                content.file_headers(),
                frozenset({FileColumn.FINAL, FileColumn.NOTES}),
                {FileColumn.FINAL: f'"{labels.stay}"'},
            ),
            content.file_rows(plan, labels),
        ),
    ]


def locked_keys(plan: ClassifyPlan, sheets: Sheets) -> list[str]:
    """The keys the `_meta` fingerprint covers: categories, event ids, row ids.

    Args:
        plan: The plan.
        sheets: Its sheets, as `sheet_specs` gives them.

    Returns:
        Them, in the workbook's order.
    """
    keys: list[str] = list(plan.categories())
    for _spec, rows in sheets[2:]:
        keys += [str(row[0]) for row in rows]
    return keys
