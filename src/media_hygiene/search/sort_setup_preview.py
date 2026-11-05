"""The tree a layout would give, on the user's own photos (0533).

From the rows of the latest `classify` plan when there is one (the names of the events
known), else from the dates of the index (years and months only). A preview only: what
`classify` proposes next may differ, as its rules see the new layout.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict

from media_hygiene.classify.layout import Values, render
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.search.days import NAME as DAY

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

    from media_hygiene.classify.plan_file import ClassifyPlan

MAIN: Final = "layout"
_NEEDS_CATEGORY: Final = "{category}"
_DATE_ONLY: Final = frozenset({SortReason.NO_SIGNAL, SortReason.DATE_ONLY})
_SHOWN: Final = 14  # lines of a tree: enough to read its shape, in a dialog
_BANDS: Final = {
    Band.SURE: (MAIN,),
    Band.UNSURE: ("unsure_layout",),
    Band.MANUAL: ("manual_layout",),
    # A plan does not say which ones a camera took: both layouts see them all.
    Band.UNDATED: ("undated_layout", "received_layout"),
}
_DATES: Final = f"SELECT {DAY}(media_date) FROM files"  # noqa: S608
_DATE_PARTS: Final = 3
_DATE_ONLY_POOL: Final = "date_only"


class TreePreview(BaseModel):
    """What one layout makes of the files it would receive."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    folders: int
    files: int
    lines: tuple[tuple[str, int], ...]  # the latest folders first, with their files


def plan_pools(plan: ClassifyPlan) -> dict[str, Counter[Values]]:
    """The files of each layout, as the plan's rows know them.

    A file only a date can place goes to the sure layout when it has no `{category}`
    (`bands.verdict`), so it has a pool of its own.

    Args:
        plan: The latest plan.

    Returns:
        By layout's key, the values of its files, counted.
    """
    pools: dict[str, Counter[Values]] = {}
    for row in plan.rows:
        if row.values is None:
            continue
        values = row.values.as_values()
        if row.reason in _DATE_ONLY:
            pools.setdefault(_DATE_ONLY_POOL, Counter())[values] += 1
            if row.band is Band.SURE:
                continue
        for key in _BANDS.get(row.band, ()):
            pools.setdefault(key, Counter())[values] += 1
    return pools


def index_pools(connection: sqlite3.Connection) -> dict[str, Counter[Values]]:
    """The dated files of the index, for the sure layout: no event known yet.

    Args:
        connection: The search's index.

    Returns:
        The pool of the sure layout.
    """
    days = Counter(day for (day,) in connection.execute(_DATES) if day)
    pool: Counter[Values] = Counter()
    for day, files in days.items():
        parts = day.split("-")
        if len(parts) == _DATE_PARTS:
            pool[Values(int(parts[0]), int(parts[1]), int(parts[2]))] += files
    return {MAIN: pool}


def preview(layout: str, key: str, pools: dict[str, Counter[Values]]) -> TreePreview:
    """The tree of one layout for one kind of files.

    Args:
        layout: The layout tried; empty: they stay, no tree.
        key: Which layout of `[classify]` it would be.
        pools: The files of each one.

    Returns:
        The number of folders and files, and the first lines.
    """
    rows: Iterable[tuple[Values, int]] = pools.get(key, Counter()).items()
    if key == MAIN and _NEEDS_CATEGORY not in layout:
        rows = (*rows, *pools.get(_DATE_ONLY_POOL, Counter()).items())
    tree: Counter[str] = Counter()
    for values, files in rows:
        folder = render(layout, values)
        if folder is not None:
            tree[folder] += files
    lines = sorted(tree.items(), reverse=True)[:_SHOWN]
    return TreePreview(folders=len(tree), files=tree.total(), lines=tuple(lines))
