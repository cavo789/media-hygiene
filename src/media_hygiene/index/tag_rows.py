"""The tags of each file, kept in the index: one row per word and source.

A source is replaced as a whole for a file (`replace`): a producer run never leaves
the words of an earlier run behind. A row of another version of the file (size or
mtime changed) reads as absent, and is replaced by the next run.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING, Final

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.tags.models import PlaceKind, Tag, TagSource

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from pathlib import Path

    from media_hygiene.index.listing import IndexedFile
    from media_hygiene.tags.models import FileTags

_DELETE: Final = "DELETE FROM tags WHERE path = ? AND source = ?"
_INSERT: Final = (
    "INSERT OR REPLACE INTO tags (path, size, mtime_ns, source, value, model, kind)"
    " VALUES (?, ?, ?, ?, ?, ?, ?)"
)
# An index of version 6 opened read-only (`search`) has no `kind` yet: read as ''.
_OF: Final = (
    "SELECT source, value, model, {kind} FROM tags"
    " WHERE path = ? AND size = ? AND mtime_ns = ? ORDER BY rowid"
)
_COLUMNS: Final = "PRAGMA table_info(tags)"
_JOINED: Final = "; "  # between two tags of a cell
# A sentence is for the search, not for a cell: the words are.
_CELL_SOURCES: Final = frozenset(TagSource) - {TagSource.CAPTION}
_COUNTS: Final = "SELECT source, COUNT(DISTINCT path) FROM tags GROUP BY source"


class TagStore:
    """Reads and replaces the tags of the index."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Bind the store to an open index.

        Args:
            connection: The index connection, tables prepared.
        """
        self._connection = connection
        columns = {row[1] for row in connection.execute(_COLUMNS)}
        self._of = _OF.format(kind="kind" if "kind" in columns else "''")

    def replace(self, sources: Iterable[TagSource], files: Sequence[FileTags]) -> int:
        """Replace the tags of some sources for some files, in one transaction.

        Args:
            sources: The sources recomputed: their old rows go, even when a file
                has no word of them any more.
            files: The files and their new tags (of those sources only).

        Returns:
            How many rows were written.
        """
        chosen = tuple(sources)
        self._connection.executemany(
            _DELETE,
            [
                (str(file.photo.path), source.value)
                for file in files
                for source in chosen
            ],
        )
        rows = [
            (
                str(file.photo.path),
                file.photo.size,
                file.photo.mtime_ns,
                tag.source.value,
                tag.value,
                tag.model,
                tag.kind.value if tag.kind is not None else "",
            )
            for file in files
            for tag in file.tags
            if tag.source in chosen
        ]
        self._connection.executemany(_INSERT, rows)
        self._connection.commit()
        return len(rows)

    def of(self, photo: PhotoVersion) -> tuple[Tag, ...]:
        """The tags of this version of a file.

        Args:
            photo: The file, with its size and mtime.

        Returns:
            Its tags, in the order they were written; empty when none (or stale).
        """
        found = self._connection.execute(
            self._of, (str(photo.path), photo.size, photo.mtime_ns)
        )
        return tuple(
            Tag(TagSource(source), str(value), str(model), _kind(kind))
            for source, value, model, kind in found
            if source in TagSource
        )

    def counts(self) -> dict[TagSource, int]:
        """How many files have tags of each source.

        Returns:
            Source → number of files (any version).
        """
        return {
            TagSource(source): int(count)
            for source, count in self._connection.execute(_COUNTS)
            if source in TagSource
        }


def _kind(value: object) -> PlaceKind | None:
    """Read the kind of a place word.

    Args:
        value: The `kind` column.

    Returns:
        The kind; None for another source, a word of an older run, or an unknown one.
    """
    kind = str(value)
    return PlaceKind(kind) if kind in PlaceKind else None


def tags_reader(connection: sqlite3.Connection) -> Callable[[IndexedFile], str | None]:
    """Read the tags of each file of an inventory, as one cell.

    Args:
        connection: The open index.

    Returns:
        File → its tags joined (the model's sentence left out), or None without any.
    """
    store = TagStore(connection)

    def read(file: IndexedFile) -> str | None:
        """Join the tags of one file.

        Args:
            file: The file and its version.

        Returns:
            The cell, or None.
        """
        photo = PhotoVersion(file.path, file.size, file.mtime_ns)
        words = dict.fromkeys(
            tag.value for tag in store.of(photo) if tag.source in _CELL_SOURCES
        )
        return _JOINED.join(words) or None

    return read


_COVERAGE: Final = (
    "SELECT COUNT(DISTINCT path), COUNT(DISTINCT CASE WHEN source = ? THEN path END)"
    " FROM tags"
)


def tag_coverage(index_file: Path | None) -> tuple[int, int] | None:
    """Count the files with words, read without changing the index file.

    Args:
        index_file: The index, None when the cache is not mounted.

    Returns:
        Files with any tag, and files with the words of the vision model; None
        without an index, or an index without tags.
    """
    if index_file is None or not index_file.is_file():
        return None
    try:
        with closing(connect_read_only(index_file)) as connection:
            row = connection.execute(_COVERAGE, (TagSource.VISION.value,)).fetchone()
    except sqlite3.Error:
        return None
    return (int(row[0]), int(row[1])) if row and row[0] else None
