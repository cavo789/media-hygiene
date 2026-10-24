"""What the index can be found by: its files, and how many have words of each source.

The page says it (0344, 0346): `chat` found nothing on an index where no photo was
described yet, and nothing said why. Each answer of the search carries the files of
the index, the files with words of each source (`vision`: what the model saw, `person`:
the names given), and whether search by meaning is on. Counted again only when the index
changed (`PRAGMA data_version`): a few tens of milliseconds on 200,000 tags (estimated);
the names, kept in memory, are counted each time (a few thousand rows).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.search import statements as sql
from media_hygiene.search.meaning_index import MeaningIndex
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.search.fts import SearchIndex

_FILES: Final = "SELECT COUNT(*) FROM files"
_BY_SOURCE: Final = "SELECT source, COUNT(DISTINCT path) FROM tags GROUP BY source"
_NAMED: Final = f"SELECT COUNT(DISTINCT path) FROM temp.{sql.PEOPLE}"  # noqa: S608


class CoverageKept:
    """The counts of an index, read again once it changed."""

    def __init__(self) -> None:
        """Nothing counted yet."""
        self._at: int | None = None
        self._files = 0
        self._sources: dict[str, int] = {}

    def of(self, search: SearchIndex) -> dict[str, object]:
        """The counts the page shows.

        Args:
            search: The open index, its names given.

        Returns:
            `files`, `sources` (files with words, by source; every source listed)
            and `meaning`.
        """
        connection = search.connection
        version = int(connection.execute(sql.DATA_VERSION).fetchone()[0])
        if version != self._at:
            self._at = version
            self._files = int(connection.execute(_FILES).fetchone()[0])
            by_source = (
                connection.execute(_BY_SOURCE).fetchall() if search.has_tags else []
            )
            self._sources = {str(name): int(count) for name, count in by_source}
        named = int(connection.execute(_NAMED).fetchone()[0])
        sources = {
            source.value: self._sources.get(source.value, 0) for source in TagSource
        }
        return {
            "files": self._files,
            "sources": {**sources, TagSource.PERSON.value: named},
            "meaning": isinstance(search, MeaningIndex) and search.understands,
        }
