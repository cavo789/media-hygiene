"""The folders a run of the tool changed: their listings are forgotten.

The walk trusts a folder's listing while its modification time is the one it saw
(`index.folder_listings`). On a Windows drive shared with Docker Desktop that time
may not change in the container when files leave or come back: the next walk would
list files a `clean` set aside, or miss those an `undo` put back. So every run that
moves, deletes or recreates files forgets the listings of the folders it touched,
where the index rows of its files are updated: the next walk reads them again.
"""

from __future__ import annotations

from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

    from media_hygiene.actions.journal import JournalEntry

_FORGET: Final = "DELETE FROM folder_listings WHERE path = ?"


def touched_folders(entries: Iterable[JournalEntry]) -> frozenset[str]:
    """The folders a run changed, in container paths.

    Args:
        entries: The actions done (`done` journal entries).

    Returns:
        The parent of every path an action read or wrote (where it was, where it
        went, its quarantine), and the path itself: a folder created or removed.
    """
    folders: set[str] = set()
    for entry in entries:
        for path in (entry.path, entry.target, entry.quarantine):
            if path:
                folders.update((path, str(PurePosixPath(path).parent)))
    return frozenset(folders)


def forget_listings(
    connection: sqlite3.Connection, entries: Iterable[JournalEntry]
) -> None:
    """Forget the listings of the folders a run changed: the next walk reads them.

    Args:
        connection: The index.
        entries: The actions done.
    """
    connection.executemany(
        _FORGET, [(folder,) for folder in sorted(touched_folders(entries))]
    )
