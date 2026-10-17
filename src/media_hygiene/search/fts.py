"""The index, searched by words: read-only, its full-text table rebuilt when stale.

The index file is opened read-only (it works on a `:ro` cache, and the search never
changes it). The full-text table is built in memory from the tags at the first search,
and again whenever another program (`tags`, `audit`) committed a change since:
`PRAGMA data_version` says so at no cost. It is never the source of truth.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING, Self

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.search import statements as sql
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.days import media_day
from media_hygiene.search.hits import hit_of
from media_hygiene.search.models import Found
from media_hygiene.search.query import match_expression

if TYPE_CHECKING:
    from collections.abc import Mapping
    from types import TracebackType

    from media_hygiene.search.query import SearchQuery


class SearchIndex:
    """Finds the files of the index by their tags."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Wrap an open index.

        Args:
            connection: The index, owned by the search from now on.
        """
        self._connection = connection
        self._built: int | None = None  # the data version the table was built at
        self._people: dict[Path, tuple[str, ...]] = {}
        connection.create_function(sql.FOLD, 1, str.casefold, deterministic=True)
        connection.create_function(DAY, 1, media_day, deterministic=True)
        connection.execute(sql.CREATE_PEOPLE)

    @classmethod
    def open(cls, index_file: Path) -> Self:
        """Open an index file read-only.

        Args:
            index_file: The index.

        Returns:
            The search.

        Raises:
            sqlite3.Error: The file cannot be read as an index.
        """
        connection = connect_read_only(index_file)
        try:
            connection.execute(sql.HAS_TAGS).fetchall()
        except sqlite3.Error:
            connection.close()
            raise
        return cls(connection)

    def __enter__(self) -> Self:
        """Use the search in a `with` block.

        Returns:
            The search itself.
        """
        return self

    def __exit__(
        self,
        exc_type: type[BaseException] | None,
        exc_val: BaseException | None,
        exc_tb: TracebackType | None,
    ) -> None:
        """Close the index.

        Args:
            exc_type: Type of the exception that ended the block, if any.
            exc_val: That exception.
            exc_tb: Its traceback.
        """
        self._connection.close()

    @property
    def has_tags(self) -> bool:
        """Tell whether the index has a table of tags (an index of 0.x before tags).

        Returns:
            True when `tags` ran at least once on an index of this version.
        """
        return self._connection.execute(sql.HAS_TAGS).fetchone() is not None

    @property
    def connection(self) -> sqlite3.Connection:
        """The open index, read-only: to read the faces.

        Returns:
            The connection.
        """
        return self._connection

    def name_people(self, words: Mapping[Path, tuple[str, ...]]) -> None:
        """Give the photos the names of the people on them, for this search only.

        Args:
            words: The names on each photo.
        """
        self._people = dict(words)
        self._connection.executemany(
            sql.PUT_PERSON,
            [(str(path), name) for path, names in words.items() for name in names],
        )
        self._built = None

    def find(self, query: SearchQuery, limit: int) -> Found:
        """Find the files matching a search.

        Args:
            query: Its words and filters.
            limit: How many files to return at most.

        Returns:
            How many match, and the first ones: best first, or newest first for a
            search without words.
        """
        self._fresh()
        conditions, parameters = sql.conditions(query)
        where = sql.WHERE + sql.AND.join(conditions) if conditions else ""
        order = sql.BEST_FIRST if match_expression(query) else sql.NEWEST_FIRST
        total = self._connection.execute(sql.COUNT + where, parameters).fetchone()[0]
        rows = self._connection.execute(
            sql.HITS + where + order + sql.LIMIT, (*parameters, limit)
        ).fetchall()
        store = TagStore(self._connection) if self.has_tags else None
        hits = tuple(hit_of((store, self._people), row) for row in rows)
        return Found(int(total), hits)

    def versions(self, query: SearchQuery) -> tuple[PhotoVersion, ...]:
        """Every file matching a search, not only the first ones: to set them aside.

        Args:
            query: Its words and filters.

        Returns:
            The files and their versions.
        """
        self._fresh()
        conditions, parameters = sql.conditions(query)
        where = sql.WHERE + sql.AND.join(conditions) if conditions else ""
        rows = self._connection.execute(sql.VERSIONS + where, parameters)
        return tuple(
            PhotoVersion(Path(path), size, mtime) for path, size, mtime in rows
        )

    def source_of(self, key: int) -> PhotoVersion | None:
        """The file a key of a hit names.

        Args:
            key: The key, from the page.

        Returns:
            The file and its version, or None for an unknown key.
        """
        row = self._connection.execute(sql.SOURCE_OF, (key,)).fetchone()
        if row is None:
            return None
        return PhotoVersion(Path(row[0]), int(row[1]), int(row[2]))

    def _fresh(self) -> None:
        """Build the full-text table, again when the index changed since."""
        version = int(self._connection.execute(sql.DATA_VERSION).fetchone()[0])
        if version == self._built:
            return
        with closing(self._connection.cursor()) as cursor:
            cursor.execute(sql.DROP)
            cursor.execute(sql.CREATE)
            cursor.execute(sql.FILL if self.has_tags else sql.FILL_PEOPLE)
        self._connection.commit()
        self._built = version
