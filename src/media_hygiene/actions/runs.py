"""Run identifiers and the per-run history derived from journals."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.actions.kinds import ACTING_PHASES, FOLDER_ACTIONS, ActionKind, Phase
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.constants import JOURNAL_SUFFIX

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry

_RUN_ID_FORMAT: Final = "%Y%m%d-%H%M%S"


def new_run_id(journal_dir: Path) -> str:
    """Create a sortable, unique run identifier such as `20260925-183015`.

    Args:
        journal_dir: Where journals live, to avoid collisions.

    Returns:
        A fresh identifier.
    """
    base = datetime.now(UTC).strftime(_RUN_ID_FORMAT)
    run_id, suffix = base, 1
    while journal_file(journal_dir, run_id).exists():
        suffix += 1
        run_id = f"{base}-{suffix}"
    return run_id


def run_phase(entries: list[JournalEntry]) -> Phase:
    """Tell which command made a run: the phase of its first action.

    Journals written before 0.3 hold `clean` entries only, and read as such.

    Args:
        entries: Journal entries, in write order.

    Returns:
        `clean` or `sort`; `clean` for a run that did nothing yet.
    """
    phases = (entry.phase for entry in entries if entry.phase in ACTING_PHASES)
    return next(phases, Phase.CLEAN)


@dataclass(frozen=True, slots=True)
class RunSummary:
    """What a run did (`clean` or `sort`), and whether it was undone."""

    run_id: str
    kind: Phase
    deleted: int
    freed: int
    quarantined: int
    moved: int
    restored: int


def summarize(journal_dir: Path, run_id: str) -> RunSummary:
    """Summarise one run from its journal.

    Args:
        journal_dir: Journal mount point.
        run_id: Identifier of the run.

    Returns:
        The run summary.
    """
    entries = read_journal(journal_file(journal_dir, run_id))
    kind = run_phase(entries)
    files = [
        entry
        for entry in done_states(entries, kind)
        if entry.action not in FOLDER_ACTIONS
    ]
    moved = [entry for entry in files if entry.action is ActionKind.MOVE]
    quarantined = [entry for entry in files if entry.action in QUARANTINED]
    deleted = len(files) - len(moved) - len(quarantined)
    return RunSummary(
        run_id=run_id,
        kind=kind,
        deleted=deleted,
        freed=sum(entry.size for entry in files if entry.action is not ActionKind.MOVE),
        quarantined=len(quarantined),
        moved=len(moved),
        restored=len(done_states(entries, Phase.UNDO)),
    )


def list_run_ids(journal_dir: Path) -> list[str]:
    """List every run that has a journal, newest first.

    Args:
        journal_dir: Journal mount point.

    Returns:
        The run identifiers.
    """
    if not journal_dir.is_dir():
        return []
    ids = (
        path.name.removesuffix(JOURNAL_SUFFIX)
        for path in journal_dir.glob(f"*{JOURNAL_SUFFIX}")
    )
    return sorted(ids, reverse=True)
