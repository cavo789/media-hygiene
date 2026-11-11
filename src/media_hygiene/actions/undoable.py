"""Whether `undo` would still put back a file of a run, checked without changing any."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.kinds import FOLDER_ACTIONS
from media_hygiene.actions.reversal import REVERSALS, Reversal, blocker, source_of
from media_hygiene.actions.undo import actions_to_undo

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry


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
    entries = read_journal_once(journal_file(journal_dir, run_id))
    folders: dict[Path, bool] = {}  # whether a source folder exists, asked once
    for entry in actions_to_undo(entries):
        reversal = REVERSALS.get(entry.action)
        if reversal is None or entry.action in FOLDER_ACTIONS:
            continue  # an unknown action, `undo` refuses it; a folder is not a file
        if reversal is Reversal.RECREATE_EMPTY or _source_folder_gone(
            entry, reversal, folders
        ):
            continue
        if blocker(entry, reversal) is None:
            return True
    return False


def _source_folder_gone(
    entry: JournalEntry, reversal: Reversal, folders: dict[Path, bool]
) -> bool:
    """Tell, with one check per folder, that the content of a file is gone.

    A purged run's quarantine folder is gone: through Docker Desktop's file sharing,
    two checks per file of every such run kept the home page waiting a minute.

    Args:
        entry: The action.
        reversal: How it is undone.
        folders: The folders checked so far (filled here).

    Returns:
        True when its source's folder does not exist (`blocker` would refuse it).
    """
    source = source_of(entry, reversal)
    if source is None:
        return False  # no source needed, or `blocker` says why
    folder = source.parent
    if folder not in folders:
        folders[folder] = folder.is_dir()
    return not folders[folder]
