"""Find the sheets and columns of a damaged workbook by their headers, in any language.

A sheet renamed, moved or with a column deleted is still recognised: each visible
sheet is compared with the headers every language of this version writes, and takes
the kind it shares the most headers with. Only the id and editable columns matter.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.workbook import rows
from media_hygiene.classify.workbook.sheets import (
    CategoryColumn,
    EventColumn,
    FileColumn,
)
from media_hygiene.classify.workbook.validation import text_of
from media_hygiene.constants import Locale
from media_hygiene.i18n import using

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence

    from media_hygiene.classify.workbook.rows import Row

# Fewer headers in common than this: not a sheet of the workbook.
_MIN_SHARED: Final = 2


class Kind(StrEnum):
    """The sheets that hold edits."""

    FILES = "files"
    EVENTS = "events"
    CATEGORIES = "categories"


class Role(StrEnum):
    """The columns read: the key and the editable ones."""

    KEY = "key"
    FINAL = "final"
    NAME = "name"
    CATEGORY = "category"
    RENAME = "rename"
    CONFIRM = "confirm"
    NOTES = "notes"


_HEADERS: Final[Mapping[Kind, Callable[[], Row]]] = {
    Kind.FILES: rows.file_headers,
    Kind.EVENTS: rows.event_headers,
    Kind.CATEGORIES: rows.category_headers,
}
_ROLES: Final[Mapping[Kind, Mapping[Role, int]]] = {
    Kind.FILES: {
        Role.KEY: FileColumn.ID,
        Role.FINAL: FileColumn.FINAL,
        Role.NOTES: FileColumn.NOTES,
    },
    Kind.EVENTS: {
        Role.KEY: EventColumn.ID,
        Role.NAME: EventColumn.NAME,
        Role.CATEGORY: EventColumn.CATEGORY,
        Role.NOTES: EventColumn.NOTES,
    },
    Kind.CATEGORIES: {
        Role.KEY: CategoryColumn.CATEGORY,
        Role.RENAME: CategoryColumn.RENAME,
        Role.CONFIRM: CategoryColumn.CONFIRM,
        Role.NOTES: CategoryColumn.NOTES,
    },
}


@dataclass(frozen=True, slots=True)
class Found:
    """A sheet recognised: its kind, and the column (0-based) of each role found."""

    kind: Kind
    columns: Mapping[Role, int]
    shared: int  # headers in common: the best sheet of a kind wins


def _fold(value: object) -> str:
    """A header, compared without case nor surrounding spaces.

    Args:
        value: A header cell.

    Returns:
        Its text, case-folded.
    """
    return text_of(value).casefold()


def _known() -> list[tuple[Kind, tuple[str, ...]]]:
    """The headers of every sheet kind, in every language.

    Returns:
        Kind and its folded headers, once per language.
    """
    known: list[tuple[Kind, tuple[str, ...]]] = []
    for locale in Locale:
        with using(locale):
            known += [
                (kind, tuple(_fold(h) for h in make()))
                for kind, make in _HEADERS.items()
            ]
    return known


def recognise(header: Sequence[object]) -> Found | None:
    """Tell which sheet a header row belongs to, and where its columns are.

    Args:
        header: The first row of a sheet.

    Returns:
        The sheet found, or None when no key column is there.
    """
    found = [_fold(value) for value in header]
    best: Found | None = None
    for kind, headers in _known():
        shared = len(set(found) & set(headers))
        if shared < _MIN_SHARED or (best is not None and shared <= best.shared):
            continue
        columns = {
            role: found.index(headers[column - 1])
            for role, column in _ROLES[kind].items()
            if headers[column - 1] in found
        }
        if Role.KEY in columns:
            best = Found(kind, columns, shared)
    return best


def best_sheets(headers: Sequence[Sequence[object]]) -> dict[Kind, tuple[int, Found]]:
    """Choose one sheet per kind: the one sharing the most headers.

    Args:
        headers: The header row of each sheet, in the workbook's order.

    Returns:
        Kind → the index of its sheet and its columns.
    """
    chosen: dict[Kind, tuple[int, Found]] = {}
    for index, header in enumerate(headers):
        found = recognise(header)
        if found is None:
            continue
        current = chosen.get(found.kind)
        if current is None or found.shared > current[1].shared:
            chosen[found.kind] = (index, found)
    return chosen
