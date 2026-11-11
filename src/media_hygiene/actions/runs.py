"""Run identifiers and the per-run history derived from journals."""

from __future__ import annotations

import re
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.actions.journal import JournalEntry, journal_file
from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.run_summary import Kept, RunSummary, run_phase, summary_of
from media_hygiene.constants import JOURNAL_SUFFIX

# Kept importable from here: every reader of the history imports them so.
__all__ = [
    "RUN_ID_PATTERN",
    "Kept",
    "RunSummary",
    "list_run_ids",
    "new_run_id",
    "run_phase",
    "summarize",
    "summary_of",
]

if TYPE_CHECKING:
    from pathlib import Path

_RUN_ID_FORMAT: Final = "%Y%m%d-%H%M%S"
# Every run identifier: the stamp, then a number when two runs share a second.
RUN_ID_PATTERN: Final = re.compile(r"\d{8}-\d{6}(?:-\d+)?")


def new_run_id(journal_dir: Path) -> str:
    """Create a unique run identifier in local time, such as `20260925-183015`.

    Args:
        journal_dir: Where journals live, to avoid collisions.

    Returns:
        A fresh identifier.
    """
    base = datetime.now().astimezone().strftime(_RUN_ID_FORMAT)
    run_id, suffix = base, 1
    while journal_file(journal_dir, run_id).exists():
        suffix += 1
        run_id = f"{base}-{suffix}"
    return run_id


def summarize(journal_dir: Path, run_id: str) -> RunSummary:
    """Summarise one run from its journal.

    Args:
        journal_dir: Journal mount point.
        run_id: Identifier of the run.

    Returns:
        The run summary.
    """
    return summary_of(read_journal_once(journal_file(journal_dir, run_id)), run_id)


def list_run_ids(journal_dir: Path) -> list[str]:
    """List every run that has a journal, newest first.

    Ordered by when each run started (UTC, in its journal), not by name: names are
    in local time, which a zone change or the autumn clock change can reorder.

    Args:
        journal_dir: Journal mount point.

    Returns:
        The run identifiers.
    """
    if not journal_dir.is_dir():
        return []
    files = journal_dir.glob(f"*{JOURNAL_SUFFIX}")
    started = {path.name.removesuffix(JOURNAL_SUFFIX): _started(path) for path in files}
    return sorted(started, key=lambda run: (started[run], run), reverse=True)


def _started(journal: Path) -> datetime:
    """When a run started: its first journal entry, else the file's last change.

    Args:
        journal: The run's journal.

    Returns:
        An aware UTC moment.
    """
    with journal.open(encoding="utf-8") as lines:
        first = lines.readline()
    try:
        return JournalEntry.model_validate_json(first).at
    except ValidationError:
        return datetime.fromtimestamp(journal.stat().st_mtime, UTC)
