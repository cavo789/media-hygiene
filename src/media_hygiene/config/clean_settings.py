"""`[clean]` — behaviour of `clean` and `undo`, and the purge reminder."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.actions.parallel import WORKERS

_PURGE_HINT_DAYS: Final = 30  # `status` suggests purging a quarantine older than that
# Left free by `clean`: a full system drive breaks Windows.
_QUARANTINE_HEADROOM_GB: Final = 1.0


class CleanSettings(BaseModel):
    """`[clean]` — behaviour of `clean` and `undo`, and the purge reminder.

    `workers` is how many files `clean`, `undo` and `sort` handle at once: four readers
    read a Windows folder ≈ 4 times faster than one (TODO 0149); a slow USB hard disk,
    whose head seeks between the readers, may prefer 1. `quarantine_headroom_gb` is
    what a `clean` copying to another drive leaves free there (0182, 0191).
    `returned`: the audit recognises the files set aside by a choice that came
    back, and `clean` sets them aside again (0216).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    confirm: bool = True
    returned: bool = True
    purge_hint_days: int = Field(default=_PURGE_HINT_DAYS, ge=1)
    workers: int = Field(default=WORKERS, ge=1)
    quarantine_headroom_gb: float = Field(default=_QUARANTINE_HEADROOM_GB, ge=0)

    @property
    def quarantine_headroom(self) -> int:
        """The space `clean` keeps free on the quarantine's drive, in bytes (0191).

        Returns:
            `quarantine_headroom_gb` GiB.
        """
        return int(self.quarantine_headroom_gb * 1024**3)
