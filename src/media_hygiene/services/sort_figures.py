"""The sorting space of the home page: sorted, in place, left (0398), kept cheap.

The figures read the latest `plan.json` (tens of megabytes for a lifetime of photos)
and the journal; they are kept until the plan or a journal file changes (a `sort`, an
`undo`), so that the home page, asked again and again, reads them once.
"""

from __future__ import annotations

from functools import lru_cache
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.actions.sort_resume import moved_rows
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.review.sort_progress import SortProgress, sort_progress

if TYPE_CHECKING:
    from pathlib import Path

_KEPT: Final = 2  # plans remembered: the latest, and the one before it
type Stamp = tuple[int, tuple[tuple[str, int], ...]]


def sort_figures(plan: Path | None, journal: Path | None) -> SortProgress | None:
    """The figures of the latest classify run.

    Args:
        plan: Its `plan.json`; None: `classify` never ran.
        journal: The journal mount point; None: not mounted (nothing sorted known).

    Returns:
        The counts; None without a readable plan.
    """
    if plan is None:
        return None
    try:
        return _figures(plan, journal, _stamp(plan, journal))
    except OSError, ValidationError:
        return None


def _stamp(plan: Path, journal: Path | None) -> Stamp:
    """What changes when the figures may change: the plan, each journal file.

    Args:
        plan: The `plan.json`.
        journal: The journal mount point, if any.

    Returns:
        The plan's mtime and each run's journal mtime.
    """
    if journal is None or not journal.is_dir():
        return plan.stat().st_mtime_ns, ()
    files = tuple(
        (run, journal_file(journal, run).stat().st_mtime_ns)
        for run in sorted(list_run_ids(journal))
    )
    return plan.stat().st_mtime_ns, files


@lru_cache(maxsize=_KEPT)
def _figures(plan: Path, journal: Path | None, _stamp: Stamp) -> SortProgress:
    """Read the plan and the journal; kept while the stamp is the same.

    Args:
        plan: The `plan.json`.
        journal: The journal mount point, if any.
        _stamp: Only a key: the figures are read again when it changes.

    Returns:
        The counts.
    """
    read = ClassifyPlan.model_validate_json(plan.read_text("utf-8"))
    moved = (
        moved_rows(journal, read.plan_id)
        if journal is not None and journal.is_dir()
        else frozenset()
    )
    return sort_progress(read, moved)
