"""The workbook's layout: sheet names, drop-down values, `_meta`, the fingerprint.

Names and values are translated when written; `_meta` records the ones used, so a
workbook written in French reads back under any locale. Columns are read by position:
the structure is locked, and `sort` matches rows by id, never by position.
"""

from __future__ import annotations

import hashlib
from dataclasses import asdict, dataclass
from enum import IntEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterable

WORKBOOK_FORMAT: Final = 1
META_SHEET: Final = "_meta"
META_LIST_COLUMN: Final = "D"  # the categories drop-down, "stay where it is" first


class MetaKey(IntEnum):
    """The rows of the `_meta` sheet (key in A, value in B)."""

    FORMAT = 1
    PLAN_ID = 2
    FINGERPRINT = 3
    SUMMARY = 4
    CATEGORIES = 5
    EVENTS = 6
    FILES = 7
    STAY = 8
    YES = 9
    NO = 10


@dataclass(frozen=True, slots=True)
class Labels:
    """The translated sheet names and drop-down values of one workbook."""

    summary: str
    categories: str
    events: str
    files: str
    stay: str
    yes: str
    no: str

    @classmethod
    def current(cls) -> Labels:
        """The labels of the active language.

        Returns:
            Them.
        """
        return cls(
            summary=_("Summary"),
            categories=_("Categories"),
            events=_("Events"),
            files=_("Files"),
            stay=_("(stay where it is)"),
            yes=_("yes"),
            no=_("no"),
        )

    def meta_rows(self, plan_id: str, digest: str) -> list[tuple[str, str]]:
        """The `_meta` key/value rows, in `MetaKey` order.

        Args:
            plan_id: The plan's id.
            digest: The fingerprint of the locked content.

        Returns:
            The rows.
        """
        values = [str(WORKBOOK_FORMAT), plan_id, digest, *asdict(self).values()]
        return [
            (key.name.lower(), value)
            for key, value in zip(MetaKey, values, strict=True)
        ]

    @classmethod
    def from_meta(cls, values: dict[MetaKey, str]) -> Labels:
        """Read the labels a workbook was written with.

        Args:
            values: The `_meta` values.

        Returns:
            The labels.
        """
        return cls(
            summary=values[MetaKey.SUMMARY],
            categories=values[MetaKey.CATEGORIES],
            events=values[MetaKey.EVENTS],
            files=values[MetaKey.FILES],
            stay=values[MetaKey.STAY],
            yes=values[MetaKey.YES],
            no=values[MetaKey.NO],
        )


class FileColumn(IntEnum):
    """The columns of the Files sheet (1-based)."""

    ID = 1
    ROOT = 2
    PROPOSAL = 10
    FINAL = 11
    NOTES = 12


class EventColumn(IntEnum):
    """The columns of the Events sheet (1-based)."""

    ID = 1
    SHARE = 5
    NAME = 9
    CATEGORY = 10
    NOTES = 11


class CategoryColumn(IntEnum):
    """The columns of the Categories sheet (1-based)."""

    CATEGORY = 1
    RENAME = 4
    CONFIRM = 5
    NOTES = 6


def fingerprint(plan_id: str, keys: Iterable[str]) -> str:
    """Fingerprint the locked keys of a workbook: its ids and categories, in order.

    Args:
        plan_id: The plan's id.
        keys: Categories, then event ids, then row ids.

    Returns:
        A SHA-256, hexadecimal.
    """
    digest = hashlib.sha256(plan_id.encode())
    for key in keys:
        digest.update(b"\x00" + key.encode())
    return digest.hexdigest()
