"""`[backup]` — what `mh backup` keeps, when it stops, how many files at once."""

from __future__ import annotations

from typing import Final

from pydantic import BaseModel, ConfigDict, Field

# The maintainer's choices (TODO 0264, 2026-10-21).
KEEP_REMOVED_DAYS: Final = 90
STOP_ABOVE_PERCENT: Final = 20
# Robocopy's own default for `/MT` is 8.
THREADS: Final = 8
_MOST_THREADS: Final = 128  # robocopy refuses more


class BackupSettings(BaseModel):
    """`[backup]` — the folder `mh backup` fills (0264).

    `keep_removed_days`: a file set aside in the backup's `.removed` (gone from the PC,
    or the previous copy of an edited file) is erased by `mh backup` after that many
    days. `stop_above_percent`: nothing is applied when the files set aside and
    replaced exceed that share of the backup (a drive missing, many files changed at
    once). `threads`: how many files robocopy copies at once (`/MT`).
    """

    model_config = ConfigDict(frozen=True, extra="forbid")

    keep_removed_days: int = Field(default=KEEP_REMOVED_DAYS, ge=0)
    stop_above_percent: int = Field(default=STOP_ABOVE_PERCENT, ge=0, le=100)
    threads: int = Field(default=THREADS, ge=1, le=_MOST_THREADS)
