"""The actions undone by moving a file back from the quarantine."""

from __future__ import annotations

import contextlib
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.kinds import ActionKind

if TYPE_CHECKING:
    from pathlib import Path

# Actions undone by moving the file back from the quarantine.
QUARANTINED: Final = frozenset(
    {ActionKind.QUARANTINE, ActionKind.QUARANTINE_NEAR}
    | {ActionKind.QUARANTINE_DUPLICATE, ActionKind.QUARANTINE_SIDECAR}
    | {ActionKind.QUARANTINE_BURST, ActionKind.QUARANTINE_JUNK},
)


def remove_emptied_folders(original: Path, quarantined: Path) -> None:
    """Remove the quarantine folders a file just left, when nothing else is in them.

    The quarantine of a run mirrors the photo folders (`<run>/c/Photos/x.jpg` for
    `/data/c/Photos/x.jpg`): the folders the two paths share by name, from the file
    up, are the quarantine's copies of the photo folders, and the run's own folder is
    next. Each is removed only while empty (`rmdir` never deletes content), so an
    undo carried out to the end leaves nothing of the run in the quarantine.

    Args:
        original: Where the file is back.
        quarantined: Where it was in the quarantine.
    """
    folder, mirrored = quarantined.parent, original.parent
    while folder.name and folder.name == mirrored.name:
        if not _removed(folder):
            return
        folder, mirrored = folder.parent, mirrored.parent
    _removed(folder)  # the run's folder, once its last file is back


def _removed(folder: Path) -> bool:
    """Remove a folder if it is empty.

    Args:
        folder: The folder.

    Returns:
        True when it was removed.
    """
    with contextlib.suppress(OSError):  # not empty, or already gone
        folder.rmdir()
        return True
    return False
