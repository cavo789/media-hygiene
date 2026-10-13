"""The listing of every folder walked, kept in the index for the next walk.

One row per folder: its modification time when listed, when it was listed, and its
entries in JSON (`[name, kind, size, mtime_ns, device, inode]`, the last four empty for
a folder). Added by index version 9.
"""

from __future__ import annotations

import json
from datetime import datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.folder_cache import (
    CachedEntry,
    CachedStat,
    EntryKind,
    FolderListing,
)

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable, Mapping

CREATE_FOLDER_LISTINGS: Final = """
CREATE TABLE IF NOT EXISTS folder_listings (
    path TEXT PRIMARY KEY,
    mtime_ns INTEGER NOT NULL,
    listed_at TEXT NOT NULL,
    entries TEXT NOT NULL
)
"""
_SELECT: Final = (
    "SELECT path, mtime_ns, listed_at, entries FROM folder_listings"
    " WHERE path = ? OR (path >= ? AND path < ?)"
)
_UPSERT: Final = (
    "INSERT OR REPLACE INTO folder_listings (path, mtime_ns, listed_at, entries)"
    " VALUES (?, ?, ?, ?)"
)
_PATHS: Final = (
    "SELECT path FROM folder_listings WHERE path = ? OR (path >= ? AND path < ?)"
)
_DELETE: Final = "DELETE FROM folder_listings WHERE path = ?"


def load_listings(
    connection: sqlite3.Connection, roots: Iterable[Path]
) -> dict[Path, FolderListing]:
    """The listings of the folders below some roots.

    Args:
        connection: The index.
        roots: The mounted folders.

    Returns:
        Each folder's listing.
    """
    found: dict[Path, FolderListing] = {}
    for root in roots:
        for path, mtime_ns, listed_at, entries in connection.execute(
            _SELECT, _below(root)
        ):
            folder = Path(path)
            found[folder] = FolderListing(
                int(mtime_ns),
                datetime.fromisoformat(listed_at),
                tuple(_entry(folder, row) for row in json.loads(entries)),
            )
    return found


def save_listings(
    connection: sqlite3.Connection,
    listings: Mapping[Path, FolderListing],
    walked: tuple[tuple[Path, ...], frozenset[Path]],
) -> None:
    """Keep the listings of the folders just read; forget the folders no longer walked.

    Args:
        connection: The index.
        listings: The folders read this time.
        walked: The roots, and every folder visited below them.
    """
    roots, visited = walked
    for root in roots:
        gone = [
            path
            for (path,) in connection.execute(_PATHS, _below(root))
            if Path(path) not in visited
        ]
        connection.executemany(_DELETE, [(path,) for path in gone])
    connection.executemany(
        _UPSERT,
        [
            (
                str(folder),
                listing.mtime_ns,
                listing.listed_at.isoformat(),
                json.dumps([_row(entry) for entry in listing.entries]),
            )
            for folder, listing in listings.items()
        ],
    )


def _below(root: Path) -> tuple[str, str, str]:
    """The query parameters of a folder and everything below it.

    Args:
        root: The folder.

    Returns:
        It, then the bounds of its descendants (`/` sorts just before `0`).
    """
    text = str(root).rstrip("/")
    return (text or "/", f"{text}/", f"{text}0")


def _row(entry: CachedEntry) -> list[str | int | None]:
    """One entry, as stored.

    Args:
        entry: The entry.

    Returns:
        `[name, kind, size, mtime_ns, device, inode]`.
    """
    facts = entry.facts
    if facts is None:
        return [entry.name, entry.kind.value, None, None, None, None]
    return [
        entry.name,
        entry.kind.value,
        facts.st_size,
        facts.st_mtime_ns,
        facts.st_dev,
        facts.st_ino,
    ]


def _entry(folder: Path, row: list[str | int | None]) -> CachedEntry:
    """One entry, read back.

    Args:
        folder: Its folder.
        row: As stored.

    Returns:
        The entry.
    """
    name, kind, size, mtime_ns, device, inode = row
    facts = (
        CachedStat(int(size), int(mtime_ns), int(device or 0), int(inode or 0))
        if size is not None and mtime_ns is not None
        else None
    )
    return CachedEntry(str(folder / str(name)), str(name), EntryKind(str(kind)), facts)
