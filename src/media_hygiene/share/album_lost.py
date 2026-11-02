"""The files of an album lost from their path, searched off the page (0547).

A page only follows a file cheaply (`album_follow`: the recorded moves, the digests
the index holds). A file the user moved, whose copies the index never fully hashed,
is searched here: one background thread, lowest priority, at most `MAX_READS` files
read in full per search, and each set of lost files searched once per run (the next
page load does not start again). What is found is saved through `write_albums`; the
page shows it from the disk at its next read.
"""

from __future__ import annotations

import contextlib
import logging
import os
import sqlite3
import threading
from concurrent.futures import ThreadPoolExecutor
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.scan.hashing import full_digest
from media_hygiene.share.album_follow import index_of
from media_hygiene.share.albums import AlbumsFile, read_albums, write_albums

if TYPE_CHECKING:
    from media_hygiene.share.album_store import AlbumStore, Shelf
    from media_hygiene.share.albums import AlbumEntry

# Files read in full by one search, at most: ~2 GB of photos, a few minutes on one
# core at the lowest priority. A constant: the next audit, or the next run, goes on.
MAX_READS: Final = 400
_SAME_SIZE: Final = "SELECT path, full_digest FROM files WHERE size = ? ORDER BY path"
_LOWEST: Final = 19
_POOL: Final = ThreadPoolExecutor(max_workers=1, thread_name_prefix="album-lost")
_ASKED: Final[set[tuple[str, frozenset[str]]]] = set()
_LOCK: Final = threading.Lock()
_LOG: Final = logging.getLogger(__name__)


def search_later(store: AlbumStore, shelf: Shelf) -> None:
    """Search the lost files of the albums in the background, once per set of them.

    Args:
        store: The albums.
        shelf: The albums as a page just read them, with their missing files.
    """
    lost = frozenset(path for paths in shelf.missing.values() for path in paths)
    asked = (str(store.place.target), lost)
    with _LOCK:
        if not lost or asked in _ASKED:
            return
        _ASKED.add(asked)
    _POOL.submit(_quietly, store)


def search_lost(store: AlbumStore) -> int:
    """Look for the lost files among the copies of the same size; save those found.

    Args:
        store: The albums.

    Returns:
        How many entries were found again.
    """
    base = read_albums(store.place.target)
    mapper = store.lookup.mapper
    found: dict[str, str] = {}
    budget = [MAX_READS]
    with index_of(store.lookup) as connection:
        if connection is None:
            return 0
        for entry in (each for album in base.albums for each in album.entries):
            if entry.path in found or mapper.to_container(entry.path).is_file():
                continue
            name = mapper.to_container(entry.path).name
            path = _same_content(connection, entry, (name, budget))
            if path is not None:
                found[entry.path] = mapper.to_host(path)
    if found:
        _relink(store, found)
    return len(found)


def _quietly(store: AlbumStore) -> None:
    """Run a search at the lowest priority; a failure is logged, never raised.

    Args:
        store: The albums.
    """
    with contextlib.suppress(OSError, AttributeError):  # Linux: per thread
        os.setpriority(os.PRIO_PROCESS, threading.get_native_id(), _LOWEST)
    try:
        search_lost(store)
    except (OSError, ValueError, sqlite3.Error) as exc:
        _LOG.warning("album search: %s", exc)


def _same_content(
    connection: sqlite3.Connection, entry: AlbumEntry, seek: tuple[str, list[int]]
) -> Path | None:
    """The copy of an entry, reading files in full within the budget.

    Args:
        connection: The index.
        entry: The entry whose path is gone.
        seek: The name it had (same name first), and the reads left.

    Returns:
        The file, in the container; None when none was found.
    """
    name, budget = seek
    rows = connection.execute(_SAME_SIZE, (entry.size,)).fetchall()
    rows.sort(key=lambda row: (Path(row[0]).name != name, row[0]))
    for path, known in rows:
        candidate = Path(path)
        if not candidate.is_file():
            continue
        digest = known
        if digest is None:
            if budget[0] <= 0:
                return None
            budget[0] -= 1
            try:
                digest = full_digest(candidate)
            except OSError:
                continue
        if digest == entry.sha256:
            return candidate
    return None


def _relink(store: AlbumStore, found: dict[str, str]) -> None:
    """Save the new paths into the albums as they are now, then follow them.

    Args:
        store: The albums.
        found: The new host path of each lost one.
    """
    base = read_albums(store.place.target)  # a page may have changed it meanwhile
    albums = tuple(
        album.model_copy(
            update={
                "entries": tuple(
                    e.model_copy(update={"path": found.get(e.path, e.path)})
                    for e in album.entries
                )
            }
        )
        for album in base.albums
    )
    write_albums(store.place.target, AlbumsFile(albums=albums))
    store.on_disk()  # two copies of one file kept once, read back
