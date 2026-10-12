"""Whether `undo` would still put back a file of a run, checked without changing any."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file, read_journal
from media_hygiene.actions.kinds import FOLDER_ACTIONS
from media_hygiene.actions.reversal import REVERSALS, Reversal, blocker
from media_hygiene.actions.undo import actions_to_undo

if TYPE_CHECKING:
    from pathlib import Path


def can_undo(journal_dir: Path, run_id: str) -> bool:
    """Tell whether `undo` would bring back at least one file of a run.

    A run counts only while the content of a file is still somewhere: after `purge`,
    its quarantined files are gone, and `undo` would only report them as skipped. An
    empty file it would recreate holds nothing: alone, it does not make a run undoable.
    The checks are those of `undo` itself (`blocker`), before it touches anything.

    Args:
        journal_dir: Journal mount point.
        run_id: Identifier of the run.

    Returns:
        True when one file action not reversed yet can still be reversed.
    """
    entries = read_journal(journal_file(journal_dir, run_id))
    for entry in actions_to_undo(entries):
        reversal = REVERSALS.get(entry.action)
        if reversal is None or entry.action in FOLDER_ACTIONS:
            continue  # an unknown action, `undo` refuses it; a folder is not a file
        if reversal is not Reversal.RECREATE_EMPTY and blocker(entry, reversal) is None:
            return True
    return False
