"""Match the rows of the previous plan to the new one: by content, the path as fallback.

A file renamed or moved since keeps its edit: its SHA-256 did not change. Two copies of
one content each find their own row (the same path first, then a free one).
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterable

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow


def row_map(old: ClassifyPlan | None, new: ClassifyPlan) -> dict[str, str]:
    """Match every row of the previous plan to a row of the new one.

    Args:
        old: The previous plan; None when it is lost (ids are then matched as they are:
            they come from the content too).
        new: The new plan.

    Returns:
        Previous row id → new row id, for the rows found.
    """
    if old is None:
        return {row.id: row.id for row in new.rows}
    by_content: defaultdict[str, list[PlanRow]] = defaultdict(list)
    for row in new.rows:
        if row.sha256:
            by_content[row.sha256].append(row)
    by_path = {row.path: row for row in new.rows}
    taken: set[str] = set()
    found: dict[str, str] = {}
    for row in _same_path_first(old.rows, by_path):
        match = _match(row, by_content.get(row.sha256 or "", []), (by_path, taken))
        if match is not None:
            taken.add(match.id)
            found[row.id] = match.id
    return found


def _same_path_first(
    rows: Iterable[PlanRow], by_path: dict[str, PlanRow]
) -> list[PlanRow]:
    """Order the previous rows: those still at their path take their row first.

    Args:
        rows: The previous rows.
        by_path: The new rows, by host path.

    Returns:
        The rows, those whose path and content are unchanged first.
    """
    return sorted(
        rows,
        key=lambda row: (
            row.path not in by_path or by_path[row.path].sha256 != row.sha256
        ),
    )


def _match(
    row: PlanRow,
    candidates: list[PlanRow],
    lookup: tuple[dict[str, PlanRow], set[str]],
) -> PlanRow | None:
    """The new row of one previous row.

    Args:
        row: A previous row.
        candidates: The new rows of the same content.
        lookup: The new rows by path, and the new rows already matched.

    Returns:
        The same content at the same path, else a free row of the same content, else
        the row at the same path; None when the file is gone.
    """
    by_path, taken = lookup
    same = by_path.get(row.path)
    if same is not None and same in candidates:
        return same
    free = [candidate for candidate in candidates if candidate.id not in taken]
    if free:
        return free[0]
    if candidates:
        return None
    return same if same is not None and same.id not in taken else None
