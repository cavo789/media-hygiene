"""The rows of a classify plan, indexed for the search page's moves (0403)."""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass
from datetime import datetime
from typing import TYPE_CHECKING

from media_hygiene.classify.models import DateSource

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow


@dataclass(frozen=True, slots=True)
class PlanRows:
    """The plan's rows by host path, and the dates of each host folder's files."""

    by_path: Mapping[str, PlanRow]
    dates: Mapping[str, tuple[datetime, ...]]


def plan_rows(plan: ClassifyPlan) -> PlanRows:
    """Index a plan's rows: by path, and the dates of each folder's files.

    Args:
        plan: The plan.

    Returns:
        The rows.
    """
    dates: dict[str, list[datetime]] = defaultdict(list)
    for row in plan.rows:
        when = taken_at(row)
        if when is not None:
            dates[parent_of(row.path)].append(when)
    return PlanRows(
        {row.path: row for row in plan.rows},
        {folder: tuple(found) for folder, found in dates.items()},
    )


def parent_of(host: str) -> str:
    r"""The folder of a host path, whatever its separators (`C:\x`, `/home/x`).

    Args:
        host: A file's host path.

    Returns:
        Its folder, written as the path is.
    """
    return host[: max(host.rfind("\\"), host.rfind("/"), 0)]


def taken_at(row: PlanRow | None) -> datetime | None:
    """The date a row was taken at, when the file says it (not the disk's date).

    Args:
        row: A row, or None.

    Returns:
        The date, or None.
    """
    if row is None or not row.date or row.date_source is DateSource.MTIME:
        return None
    return datetime.fromisoformat(row.date)
