"""Why a file of the backup is no longer on the PC, as the tool knows it (0264).

Only the files the user removed on purpose are proposed for removal from the backup:
purged from the quarantine (or deleted by `clean` as an exact copy), or confirmed
deleted in `review --gone`. A file still in the quarantine, a deletion not confirmed
yet, or one the tool knows nothing of stays: a deletion by mistake in the Explorer is
never carried over to the backup.
"""

from __future__ import annotations

from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from media_hygiene.plan.push_entries import Entry


class GoneReason(StrEnum):
    """What the tool knows of a file the PC no longer has, most certain first."""

    PURGED = "purged"  # its quarantine erased by `purge`, or deleted by `clean`
    CONFIRMED = "confirmed"  # deleted in the Explorer, confirmed in `review --gone`
    QUARANTINE = "quarantine"  # set aside by `clean`, its quarantine still there
    PENDING = "pending"  # deleted in the Explorer, `review --gone` not answered yet
    UNKNOWN = "unknown"  # nothing: a deletion by mistake, a folder renamed by hand…

    @property
    def proposed(self) -> bool:
        """Tell whether a file gone so is proposed for removal from the backup.

        Returns:
            True when purged or confirmed.
        """
        return self in {GoneReason.PURGED, GoneReason.CONFIRMED}


@dataclass(frozen=True, slots=True)
class Gone:
    """A file of the backup the PC no longer has, and why."""

    entry: Entry
    reason: GoneReason
