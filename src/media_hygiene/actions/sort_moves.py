"""The journaled changes of a sort: a file moved, a folder created, never overwriting.

On one disk a file is renamed (instant, atomic); across disks (two Docker mounts are two
disks, even on one drive) it is copied, proven identical, then removed, and its SHA-256
is journaled so that `undo` and the manifest can prove it whole.
"""

from __future__ import annotations

import errno
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.journaled import JournaledChanges
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.quarantine import move_verified
from media_hygiene.constants import MediaKind
from media_hygiene.i18n import _
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.actions.outcome import Tally


@dataclass(frozen=True, slots=True)
class SortContext:
    """The journal of the run (phase `sort`), the plan applied, the stop request."""

    changes: CleanContext
    plan_id: str
    stop: Callable[[], bool]  # True once Ctrl+C was pressed


def file_of(path: Path, stat: tuple[int, int] | None = None) -> MediaFile:
    """Describe a file (or a folder) for the journal.

    Args:
        path: Its path.
        stat: Its size and modification time as seen before; read now when None.

    Returns:
        The description.
    """
    if stat is None:
        info = path.stat()
        stat = (info.st_size, info.st_mtime_ns)
    return MediaFile(path, *stat, media_kind(path) or MediaKind.OTHER)


class Relocator:
    """Numbers, journals and counts the moves and folders of one sort run."""

    def __init__(self, context: SortContext, tally: Tally) -> None:
        """Prepare the changes of a run.

        Args:
            context: Journal, plan and stop request.
            tally: Counters of the run.
        """
        self._context = context
        self._tally = tally
        self.changes = JournaledChanges(context.changes, tally)

    def move(
        self, file: MediaFile, target: Path, row: str | None = None
    ) -> JournalEntry:
        """Move a file, journaled.

        Args:
            file: The file.
            target: Where it goes; never overwritten.
            row: Its row in the plan (None for a sidecar).

        Returns:
            The journal entry of the move.

        Raises:
            FileExistsError: Something is at the target already.
            OSError: The move failed (the journal keeps it `pending`).
        """
        if os.path.lexists(target):
            raise FileExistsError(errno.EEXIST, _("the target exists"), str(target))
        self.make_folder(target.parent)
        entry = self.changes.entry(file, ActionKind.MOVE).model_copy(
            update={"target": str(target), "plan": self._context.plan_id, "row": row}
        )
        journal = self._context.changes.journal
        journal.record(entry)
        try:
            file.path.rename(target)
        except OSError as exc:
            if exc.errno != errno.EXDEV:
                raise
            entry = entry.model_copy(update={"sha256": full_digest(file.path)})
            journal.record(entry)
            move_verified(file.path, target)
        journal.record(entry.as_done())
        self._tally.done += 1
        self._tally.bytes_done += file.size
        return entry

    def make_folder(self, folder: Path) -> None:
        """Create a folder and its missing parents, each one journaled.

        Args:
            folder: The folder.
        """
        missing: list[Path] = []
        while not folder.exists():
            missing.append(folder)
            folder = folder.parent
        for created in reversed(missing):
            entry = self.changes.entry(
                file_of(created, (0, 0)), ActionKind.CREATE_FOLDER
            )
            self.changes.record(entry, created.mkdir)
