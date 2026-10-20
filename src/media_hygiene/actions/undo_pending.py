"""Whether a `pending` action of a run stopped halfway changed anything at all."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.copy_in_undo import never_copied
from media_hygiene.actions.kinds import Status
from media_hygiene.actions.link_undo import never_linked
from media_hygiene.actions.reversal import XMP_REVERSALS, Reversal
from media_hygiene.actions.xmp_undo import never_written

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

# Undone by removing what the action created: the path existing proves it happened.
_NOT_ABOUT_THE_PATH: Final = frozenset(
    {Reversal.REMOVE_CREATED_FOLDER, Reversal.REMOVE_LINK, Reversal.REMOVE_MARKER}
)


def never_happened(entry: JournalEntry, reversal: Reversal) -> bool:
    """Tell whether a run stopped before this action changed anything.

    A `pending` action may have happened (stopped before its `done` line) or not
    (stopped before it acted). A file still where the action would have taken it
    from was never touched: there is nothing to undo, and nothing to warn about. A
    copy made a link keeps its name either way: only its identity tells (0213).

    Args:
        entry: Latest state of the action.
        reversal: How it is undone.

    Returns:
        True for a `pending` file action whose file is still in place.
    """
    if reversal in XMP_REVERSALS:
        return never_written(entry)
    if reversal is Reversal.SEPARATE_LINK:
        return never_linked(entry)
    if reversal is Reversal.REMOVE_COPY:
        return never_copied(entry)
    return (
        entry.status is Status.PENDING
        and reversal not in _NOT_ABOUT_THE_PATH
        and Path(entry.path).exists()
    )
