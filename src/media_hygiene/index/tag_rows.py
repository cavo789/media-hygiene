"""The tags of each file, kept in the index: one row per word and source.

A source is replaced as a whole for a file (`replace`): a producer run never leaves
the words of an earlier run behind. A row of another version of the file (size or
mtime changed) reads as absent, and is replaced by the next run.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.tags.models import Tag, TagSource

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Iterable, Sequence

    from media_hygiene.index.listing import IndexedFile
    from media_hygiene.tags.models import FileTags

_DELETE: Final = "DELETE FROM tags WHERE path = ? AND source = ?"
_INSERT: Final = (
    "INSERT OR REPLACE INTO tags (path, size, mtime_ns, source, value, model)"
    " VALUES (?, ?, ?, ?, ?, ?)"
)
_OF: Final = (
    "SELECT source, value, model FROM tags"
    " WHERE path = ? AND size = ? AND mtime_ns = ? ORDER BY rowid"
)
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
            _OF, (str(photo.path), photo.size, photo.mtime_ns)
        )
        return tuple(
            Tag(TagSource(source), str(value), str(model))
            for source, value, model in found
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
