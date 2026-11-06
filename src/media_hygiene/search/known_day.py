"""The day of a file: its own date, else the one its `.xmp` sidecar holds (0531).

The sidecars' days live in a temporary table, read from the disk at the start and at
each ask (`sidecar_days`): the index is never written, and a file's own date always
wins.
"""

from __future__ import annotations

from typing import Final

from media_hygiene.classify.hand_days import CREATE as CREATE_DAYS
from media_hygiene.classify.hand_days import TABLE as SIDECAR_DAYS
from media_hygiene.search.days import NAME as DAY

__all__ = ["CREATE_DAYS", "SIDECAR_DAYS"]
CLEAR_DAYS: Final = f"DELETE FROM temp.{SIDECAR_DAYS}"  # noqa: S608
PUT_DAY: Final = f"INSERT INTO temp.{SIDECAR_DAYS} (path, day) VALUES (?, ?)"  # noqa: S608
KNOWN_DAY: Final = (
    f"COALESCE({DAY}(files.media_date), (SELECT d.day FROM temp.{SIDECAR_DAYS} AS d"  # noqa: S608
    " WHERE d.path = files.path))"
)
UNDATED: Final = f"{KNOWN_DAY} IS NULL"
OWN_UNDATED: Final = f"SELECT path FROM files WHERE {DAY}(media_date) IS NULL"  # noqa: S608
