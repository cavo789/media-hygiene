"""`import <folder> --since`: only the copies of a period (0476).

A folder's file has the same day as a phone's: the date in its name, else its
modified time. Without `--since` a folder import takes every file: unlike a phone, a
NAS or an old disk holds years never imported, which "since the last import" would hide.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import UTC, datetime
from typing import TYPE_CHECKING

from media_hygiene.services.import_since import first_day, kept, today_local

if TYPE_CHECKING:
    from media_hygiene.services.import_plan import ImportPlan


def within(plan: ImportPlan, since: str | None) -> tuple[ImportPlan, int]:
    """Keep the copies of the period.

    Args:
        plan: Every copy the import proposes.
        since: `--since` as typed; None: every file.

    Returns:
        The plan of the period, and how many files were left out (older).
    """
    if since is None:
        return plan, 0
    first = first_day(since, today_local(), None)
    jobs = tuple(
        job
        for job in plan.jobs
        if kept(
            job.source.name,
            datetime.fromtimestamp(job.source.stat().st_mtime, UTC).isoformat(),
            first,
        )
    )
    return replace(plan, jobs=jobs), len(plan.jobs) - len(jobs)
