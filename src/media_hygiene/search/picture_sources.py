"""Which file a picture's key names, on a connection of its own (2026-11-16).

The library's thumbnails looked their file up on the page's one connection: while a
search or the places held it in their thread, each thumbnail waited, and the event
loop with it (1.6 to 3.6 s per batch of thumbnails, measured on the maintainer's PC).
A second read-only connection to the same index reads beside them: SQLite lets
several connections read at once.
"""

from __future__ import annotations

import contextlib
import sqlite3
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final, Protocol

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.search import statements as sql

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex

_MAIN_FILE: Final = "SELECT file FROM pragma_database_list WHERE name = 'main'"


class Sources(Protocol):
    """Anything that names the file of a picture's key."""

    def source_of(self, key: int) -> PhotoVersion | None:
        """The file a key names.

        Args:
            key: The key, from the page.

        Returns:
            The file and its version, or None for an unknown key.
        """


@dataclass(slots=True)
class PictureSources:
    """The library's picture lookups, each on a short connection of its own."""

    index: SearchIndex
    _file: Path | None = field(default=None)  # the index file, read once
    _asked: bool = field(default=False)

    def source_of(self, key: int) -> PhotoVersion | None:
        """The file a key names, without waiting for the page's connection.

        Opening the index read-only costs a fraction of a millisecond (it lives in
        `/cache`, never on the Windows mount); one connection per lookup is never
        left open after the page.

        Args:
            key: The key, from the page.

        Returns:
            The file and its version, or None for an unknown key.
        """
        file = self._index_file()
        if file is None:  # an index in memory (tests): the page's connection
            return self.index.source_of(key)
        try:
            with contextlib.closing(connect_read_only(file)) as connection:
                row = connection.execute(sql.SOURCE_OF, (key,)).fetchone()
        except sqlite3.Error:
            return self.index.source_of(key)
        if row is None:
            return None
        return PhotoVersion(Path(row[0]), int(row[1]), int(row[2]))

    def _index_file(self) -> Path | None:
        """The index's file, asked of the page's connection once.

        Returns:
            It; None when the index has no file to open again.
        """
        if not self._asked:
            row = self.index.connection.execute(_MAIN_FILE).fetchone()
            self._file = Path(row[0]) if row and row[0] else None
            self._asked = True
        return self._file
