"""The day an undated file's `.xmp` sidecar holds, as the index's readers see it (0618).

The days are read from the disk by the search page (`search/sidecar_days`) into a
temporary table of its connection, never into the index file. The event finders read
it beside `media_date`: a file's own date always wins, a hand-set day comes next.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from datetime import datetime

TABLE: Final = "sidecar_days"
_COLUMNS: Final = "(path TEXT PRIMARY KEY, day TEXT NOT NULL)"
CREATE: Final = f"CREATE TEMP TABLE IF NOT EXISTS {TABLE} {_COLUMNS}"
SIDECAR_DAY: Final = (
    f"(SELECT d.day FROM temp.{TABLE} AS d"  # noqa: S608
    " WHERE d.path = files.path)"
)
_NOON: Final = 12  # a day without a time, as `classify` dates it


def ready(connection: sqlite3.Connection) -> sqlite3.Connection:
    """Make sure the connection holds the table (empty on a bare index).

    Args:
        connection: The index.

    Returns:
        It.
    """
    connection.execute(CREATE)
    return connection


def known(own: datetime | None, hand: datetime | None) -> datetime | None:
    """A file's own date, else the day set by hand, at noon.

    Args:
        own: Its EXIF or video date.
        hand: The day of its sidecar, at midnight.

    Returns:
        The moment it counts at; None when neither says one.
    """
    if own is not None:
        return own
    return hand.replace(hour=_NOON) if hand is not None else None
