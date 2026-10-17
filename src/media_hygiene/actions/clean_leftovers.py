"""The files a clean handles besides copies: broken files and orphan sidecars."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.outcome import Incident
from media_hygiene.actions.verify import change_blocker, orphan_blocker
from media_hygiene.constants import BrokenReason

if TYPE_CHECKING:
    from media_hygiene.actions.journaled import JournaledChanges
    from media_hygiene.actions.outcome import Tally
    from media_hygiene.scan.models import BrokenFile, MediaFile


@dataclass(frozen=True, slots=True)
class Leftovers:
    """Deletes empty files, moves unreadable files and orphan sidecars aside."""

    changes: JournaledChanges
    tally: Tally

    def broken(self, item: BrokenFile) -> None:
        """Delete an empty file, or move an unreadable one to the quarantine.

        Args:
            item: The broken file.
        """
        blocker = change_blocker(item.file)
        if blocker is not None:
            self.tally.skipped.append(Incident(item.file.path, blocker))
            return
        if item.reason is BrokenReason.EMPTY:
            entry = self.changes.entry(item.file, ActionKind.DELETE_EMPTY)
            self.changes.act(entry, item.file.path.unlink)
            return
        self.changes.quarantine(item.file, ActionKind.QUARANTINE)

    def orphan(self, sidecar: MediaFile) -> None:
        """Move an orphan sidecar to the quarantine, where `undo` finds it again.

        Args:
            sidecar: The sidecar, as audited.
        """
        blocker = orphan_blocker(sidecar)
        if blocker is not None:
            self.tally.skipped.append(Incident(sidecar.path, blocker))
            return
        self.changes.quarantine(sidecar, ActionKind.QUARANTINE_SIDECAR)
