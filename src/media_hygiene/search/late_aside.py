"""*New photos during an event* leaves out the files set aside (0518).

A file set aside is a soft delete: it is never proposed to an event, and an event
whose late files are all set aside is not proposed at all.
"""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.classify.late_files import LateEvent
    from media_hygiene.paths.host_paths import HostPathMapper

_PATH: Final = "SELECT path FROM files WHERE rowid = ?"


def without_aside(
    connection: sqlite3.Connection,
    found: list[LateEvent],
    aside: tuple[HostPathMapper, frozenset[str]],
) -> list[LateEvent]:
    """The events' late files, those set aside left out; emptied events dropped.

    Args:
        connection: The index.
        found: The events with late files.
        aside: The host paths' mapper and the host paths set aside.

    Returns:
        The events still holding a late file.
    """
    mapper, chosen = aside
    if not chosen:
        return found

    def kept(key: int) -> bool:
        """Whether the file of an index key is not set aside.

        Args:
            key: Its index key.

        Returns:
            True for a file not set aside (or gone from the index).
        """
        row = connection.execute(_PATH, (key,)).fetchone()
        return row is None or mapper.to_host(Path(row[0])) not in chosen

    events = (
        replace(event, files=tuple(file for file in event.files if kept(file.key)))
        for event in found
    )
    return [event for event in events if event.files]
