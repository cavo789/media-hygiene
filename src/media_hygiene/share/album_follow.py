"""Find again the files of an album that moved, by what the index knows (0295).

A file still at its path is kept as it is. One gone from it is looked for, in order:
the moves the index recorded (`sort`, `undo`: `index.moves`), then the files of the
same size whose SHA-256 is the entry's (the index's digest when it has one, else the
file read once): a folder renamed in the Explorer is found after the next audit. Among
identical copies, the one of the same name first, then the first path: the same
answer every time. Not found: the entry stays, said missing, never dropped.
"""

from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Iterable, Iterator

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.share.albums import AlbumEntry

_MOVED: Final = "SELECT new FROM moves WHERE old = ?"
_SAME_SIZE: Final = "SELECT path, full_digest FROM files WHERE size = ? ORDER BY path"
_KNOWN: Final = (
    "SELECT full_digest FROM files WHERE path = ? AND size = ? AND mtime_ns = ?"
)
_MAX_HOPS: Final = 8  # a file moved by `sort`, then again: a short chain


@dataclass(frozen=True, slots=True)
class Lookup:
    """Where to look: the index file (None: none yet), and the paths' two forms."""

    index_file: Path | None
    mapper: HostPathMapper


@dataclass(frozen=True, slots=True)
class Followed:
    """The entries of an album, those found again at their new path."""

    entries: tuple[AlbumEntry, ...]
    missing: tuple[str, ...]  # the host paths of the entries not found
    changed: bool  # a path was updated: the file is to save


@contextlib.contextmanager
def index_of(lookup: Lookup) -> Iterator[sqlite3.Connection | None]:
    """Open the index read-only for one pass, or nothing without one.

    Args:
        lookup: Where the index is.

    Yields:
        The connection, or None.
    """
    connection = None
    if lookup.index_file is not None and lookup.index_file.is_file():
        with contextlib.suppress(sqlite3.Error):
            connection = connect_read_only(lookup.index_file)
    try:
        yield connection
    finally:
        if connection is not None:
            connection.close()


def digest_of(connection: sqlite3.Connection | None, source: Path) -> str:
    """The SHA-256 of a file: the index's when it knows this version, else read.

    Args:
        connection: The index, or None.
        source: The file, in the container.

    Returns:
        Its hex digest.

    Raises:
        OSError: The file cannot be read.
    """
    if connection is not None:
        stat = source.stat()
        with contextlib.suppress(sqlite3.Error):
            row = connection.execute(
                _KNOWN, (str(source), stat.st_size, stat.st_mtime_ns)
            ).fetchone()
            if row is not None and row[0]:
                return str(row[0])
    return full_digest(source)


def follow(entries: Iterable[AlbumEntry], lookup: Lookup) -> Followed:
    """Check each entry; follow the ones whose file moved.

    Args:
        entries: The entries of one album.
        lookup: The index and the mapper.

    Returns:
        The entries (a moved one at its new path), and those missing.
    """
    kept: list[AlbumEntry] = []
    missing: list[str] = []
    changed = False
    with index_of(lookup) as connection:
        for entry in entries:
            if lookup.mapper.to_container(entry.path).is_file():
                kept.append(entry)
                continue
            found = None if connection is None else _seek(connection, entry, lookup)
            if found is None:
                kept.append(entry)
                missing.append(entry.path)
                continue
            kept.append(entry.model_copy(update={"path": lookup.mapper.to_host(found)}))
            changed = True
    unique = {entry.path: entry for entry in reversed(kept)}  # two copies, one file
    return Followed(
        tuple(e for e in kept if unique.get(e.path) is e),
        tuple(missing),
        changed or len(unique) != len(kept),
    )


def _seek(
    connection: sqlite3.Connection, entry: AlbumEntry, lookup: Lookup
) -> Path | None:
    """Where the file of an entry is now.

    Args:
        connection: The index.
        entry: The entry whose path is gone.
        lookup: The mapper.

    Returns:
        The file, in the container; None when nothing holds the same content.
    """
    old = lookup.mapper.to_container(entry.path)
    moved = _moved(connection, str(old))
    if moved is not None and moved.is_file() and moved.stat().st_size == entry.size:
        return moved
    return _same_content(connection, entry, old.name)


def _same_content(
    connection: sqlite3.Connection, entry: AlbumEntry, name: str
) -> Path | None:
    """The file of the same size and SHA-256 as an entry: the same name first.

    Args:
        connection: The index.
        entry: The entry whose path is gone.
        name: The name the file had.

    Returns:
        The file, in the container; None when nothing holds the same content.
    """
    try:
        rows = connection.execute(_SAME_SIZE, (entry.size,)).fetchall()
    except sqlite3.Error:
        return None
    rows.sort(key=lambda row: (Path(row[0]).name != name, row[0]))
    for path, digest in rows:
        candidate = Path(path)
        if not candidate.is_file():
            continue
        try:
            same = (digest or full_digest(candidate)) == entry.sha256
        except OSError:
            continue
        if same:
            return candidate
    return None


def _moved(connection: sqlite3.Connection, old: str) -> Path | None:
    """Follow the moves the index recorded from a path.

    Args:
        connection: The index.
        old: The path the file had, in the container.

    Returns:
        The last path it was moved to, or None.
    """
    path: str | None = None
    current = old
    with contextlib.suppress(sqlite3.Error):  # an index older than the table
        for _hop in range(_MAX_HOPS):
            row = connection.execute(_MOVED, (current,)).fetchone()
            if row is None:
                break
            path = current = str(row[0])
    return None if path is None else Path(path)
