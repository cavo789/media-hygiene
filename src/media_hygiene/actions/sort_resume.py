"""Resume a sort: the rows earlier runs of the same plan moved, and did not undo."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import (
    done_states,
    journal_file,
    latest_states,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import list_run_ids, run_phase

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


def moved_rows(journal_dir: Path, plan_id: str) -> frozenset[str]:
    """List the rows of a plan that earlier `sort` runs moved.

    A move the journal left `pending` (the container was killed in the middle) counts
    when the file is at its target and no longer at its source.

    Args:
        journal_dir: Journal mount point.
        plan_id: The classify plan.

    Returns:
        Their row ids; moves undone since are not listed.
    """
    return frozenset(moved_targets(journal_dir, plan_id))


def moved_targets(journal_dir: Path, plan_id: str) -> dict[str, Path]:
    """Tell where earlier `sort` runs of a plan moved its rows.

    Args:
        journal_dir: Journal mount point.
        plan_id: The classify plan.

    Returns:
        Row id → where its file is now (container path); moves undone are left out.
    """
    targets: dict[str, Path] = {}
    for run_id in sorted(list_run_ids(journal_dir)):
        entries = read_journal(journal_file(journal_dir, run_id))
        if run_phase(entries) is not Phase.SORT:
            continue
        undone = {entry.seq for entry in done_states(entries, Phase.UNDO)}
        targets |= {
            entry.row: Path(entry.target or entry.path)
            for seq, entry in latest_states(entries, Phase.SORT).items()
            if entry.row and seq not in undone and _moved(entry, plan_id)
        }
    return targets


def _moved(entry: JournalEntry, plan_id: str) -> bool:
    """Tell whether an entry is a move of this plan that happened.

    Args:
        entry: The latest state of an action.
        plan_id: The classify plan.

    Returns:
        True for a move of the plan, done, or pending but carried out.
    """
    if entry.action is not ActionKind.MOVE or entry.plan != plan_id:
        return False
    if entry.status is Status.DONE:
        return True
    return entry.target is not None and (
        Path(entry.target).is_file() and not Path(entry.path).exists()
    )
