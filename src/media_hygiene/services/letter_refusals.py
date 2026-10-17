"""What the undo of a run under a drive's new letter refuses to bring back (0186, 0202).

A file comes back only when its folder is on the drive under the new letter: never
onto another drive's path by guess. A folder the run itself removed once it left it
empty (`clean`, `sort`) counts: the undo recreates it first, when its own parent is
there.
"""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.quarantine import QUARANTINED

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry


# The files an undo brings back from the quarantine or rebuilds from their keeper.
COMES_BACK: Final = QUARANTINED | {ActionKind.DELETE_DUPLICATE}
# Also what the undo recreates empty: an empty file, a folder the run removed.
_NEEDS_A_FOLDER: Final = COMES_BACK | {
    ActionKind.DELETE_EMPTY,
    ActionKind.REMOVE_FOLDER,
}


def refused(moved: list[JournalEntry], entries: list[JournalEntry]) -> dict[int, Path]:
    """List the actions whose folder is missing under the new letter.

    Args:
        moved: The run's journal, written under the new letters.
        entries: The same journal, as the run wrote it.

    Returns:
        The path of each refused action, by its sequence number; a move of `sort`
        comes back on its own drive and is never refused.
    """
    changed = [
        entry
        for entry, before in zip(moved, entries, strict=True)
        if entry.path != before.path
    ]
    recreated = frozenset(
        Path(entry.path)
        for entry in changed
        if entry.action is ActionKind.REMOVE_FOLDER
    )
    return {
        entry.seq: Path(entry.path)
        for entry in changed
        if entry.action in _NEEDS_A_FOLDER
        and not _there(Path(entry.path).parent, recreated)
    }


def _there(folder: Path, recreated: frozenset[Path]) -> bool:
    """Tell whether a folder exists, or will once the undo recreated it.

    Args:
        folder: A folder under the new letter.
        recreated: The folders the run removed, which the undo recreates.

    Returns:
        True when the first folder above it that the run did not remove exists.
    """
    while folder in recreated:
        folder = folder.parent
    return folder.is_dir()
