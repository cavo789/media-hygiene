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
from typing import TYPE_CHECKING, Final, Self

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.index.read_only import connect_read_only
from media_hygiene.index.tag_rows import TagStore
from media_hygiene.search import statements as sql
from media_hygiene.search.models import Found, Hit
from media_hygiene.search.query import match_expression

if TYPE_CHECKING:
    from types import TracebackType

    from media_hygiene.search.query import SearchQuery
    from media_hygiene.tags.models import TagSource

_DATE_LENGTH: Final = 10  # `YYYY:MM:DD`, then the time
_EXIF_SEPARATOR, _DATE_SEPARATOR = ":", "-"


class SearchIndex:
    """Finds the files of the index by their tags."""

    def __init__(self, connection: sqlite3.Connection) -> None:
        """Wrap an open index.

        Args:
            connection: The index, owned by the search from now on.
        """
        self._connection = connection
        self._built: int | None = None  # the data version the table was built at
        connection.create_function(sql.FOLD, 1, str.casefold, deterministic=True)

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
        store = TagStore(self._connection)
        hits = tuple(_hit(store, row) for row in rows)
        return Found(int(total), hits)

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
            if self.has_tags:
                cursor.execute(sql.FILL)
        self._connection.commit()
        self._built = version


def _hit(store: TagStore, row: tuple[object, ...]) -> Hit:
    """Make a hit of a row, with the tags of the file.

    Args:
        store: The tags of the index.
        row: Key, path, size, mtime and date of a file.

    Returns:
        The hit.
    """
    key, path, size, mtime_ns, taken = row
    photo = PhotoVersion(Path(str(path)), int(str(size)), int(str(mtime_ns)))
    tags: dict[TagSource, list[str]] = {}
    for tag in store.of(photo):
        tags.setdefault(tag.source, []).append(tag.value)
    date = (
        str(taken)[:_DATE_LENGTH].replace(_EXIF_SEPARATOR, _DATE_SEPARATOR)
        if taken
        else None
    )
    return Hit(
        int(str(key)),
        photo,
        date,
        {source: tuple(values) for source, values in tags.items()},
    )
