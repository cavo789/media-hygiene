"""A partial undo (0525): the quarantined files of a run picked one by one.

`undo <run>` reverses every action of a run not reversed yet; a pick keeps only the
actions it names (by their sequence number in the journal), so the `undo` entries the
executor writes are those of the files picked. `actions_to_undo` then leaves them out:
a later `undo` of the run puts back the rest, never these twice.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.reversal import REVERSALS, Reversal
from media_hygiene.actions.undo import actions_to_undo

if TYPE_CHECKING:
    from collections.abc import Collection

    from media_hygiene.actions.journal import JournalEntry


@dataclass(frozen=True, slots=True)
class RunPick:
    """What an undo takes back: a run, and the actions picked (None: all of them)."""

    run_id: str
    seqs: frozenset[int] | None = None


def picked_entries(
    entries: list[JournalEntry], seqs: Collection[int] | None
) -> list[JournalEntry]:
    """Keep the journal lines of the actions picked, and of the folders they need.

    A clean removes the folders it emptied: a file picked comes back with the folder
    it lay in, so that folder's removal is reversed with it (journaled), or a later
    `undo` of the run would find it there already and call it skipped.

    Args:
        entries: Every entry of the run's journal.
        seqs: The sequence numbers picked; None keeps every entry.

    Returns:
        The entries of those actions only, in the journal's order.
    """
    if seqs is None:
        return entries
    folders = {
        parent
        for entry in entries
        if entry.seq in seqs
        for parent in Path(entry.path).parents
    }
    return [
        entry
        for entry in entries
        if entry.seq in seqs
        or (entry.action is ActionKind.REMOVE_FOLDER and Path(entry.path) in folders)
    ]


def quarantined_now(entries: list[JournalEntry]) -> list[JournalEntry]:
    """List the files of a run still in the quarantine, not put back yet.

    Args:
        entries: Every entry of the run's journal.

    Returns:
        The latest state of each quarantine move whose file is still there.
    """
    return [
        entry
        for entry in actions_to_undo(entries)
        if REVERSALS.get(entry.action) is Reversal.UNQUARANTINE
        and entry.quarantine
        and Path(entry.quarantine).is_file()
    ]
