"""The search with meaning: names and places narrow, the meaning ranks (TODO 0263).

"Frédérique dans la cuisine": `Frédérique` is a person's name (a word of the `person`
or `place` column), so only her photos count; the other words (`dans la cuisine`) are
understood by the model and rank them, kitchens first, merged with today's words by
reciprocal rank fusion. A search of names and places only, a search among one
source, or an index without vectors is the full-text search as before.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final, override

from media_hygiene.index.tag_rows import TagStore
from media_hygiene.search import statements as sql
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.hits import hit_of
from media_hygiene.search.meaning import Meaning, fused
from media_hygiene.search.models import Found
from media_hygiene.search.query import SearchQuery, Term, term_expression
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.search.meaning import MeaningSource

NARROWING: Final = (TagSource.PERSON, TagSource.PLACE)
_COLUMNS: Final = "{" + " ".join(source.value for source in NARROWING) + "}"


class MeaningIndex(SearchIndex):
    """Finds the files by their words, and ranks them by what they show."""

    _meaning: Meaning | None = None
    _read_at: int | None = None  # the data version the vectors were read at

    def understand(self, source: MeaningSource) -> None:
        """Rank by meaning from now on.

        Args:
            source: How to load the text model, how many photos at most.
        """
        self._meaning = Meaning(source)

    @override
    def find(self, query: SearchQuery, limit: int) -> Found:
        """Find the files matching a search, by meaning when it has any.

        Args:
            query: Its words and filters.
            limit: How many files to return at most.

        Returns:
            How many match, and the first ones, best first.
        """
        keys = self._ranked(query)
        if keys is None:
            return super().find(query, limit)
        store = TagStore(self._connection) if self.has_tags else None
        shown = keys[:limit]
        rows = (
            self._connection.execute(sql.HIT_OF, (key,)).fetchone() for key in shown
        )
        hits = tuple(
            hit_of((store, self._people), row) for row in rows if row is not None
        )
        return Found(len(keys), hits)

    @override
    def versions(self, query: SearchQuery) -> tuple[PhotoVersion, ...]:
        """Every file a search finds, by meaning when it has any: to set them aside.

        Args:
            query: Its words and filters.

        Returns:
            The files and their versions.
        """
        keys = self._ranked(query)
        if keys is None:
            return super().versions(query)
        found = (self.source_of(key) for key in keys)
        return tuple(photo for photo in found if photo is not None)

    def _ranked(self, query: SearchQuery) -> tuple[int, ...] | None:
        """The files of a search by meaning, best first.

        Args:
            query: Its words and filters.

        Returns:
            Their rows; None when the words alone answer it.
        """
        meaning = self._meaning
        if meaning is None or not query.terms or query.filters.source is not None:
            return None
        self._fresh()
        if self._read_at != self._built:
            meaning.read(self._connection)
            self._read_at = self._built
        narrow = tuple(term for term in query.terms if self._narrows(term))
        rest = [term.text for term in query.terms if term not in narrow]
        if not rest:
            return None
        pool = self._keys(SearchQuery(narrow, query.filters))
        allowed = None if pool is None else frozenset(pool)
        closest = meaning.closest(" ".join(rest), allowed)
        if closest is None:
            return None
        words = self._keys(query) or ()
        return fused((words, closest))

    def _narrows(self, term: Term) -> bool:
        """Tell whether a term names a person or a place of the index.

        Args:
            term: A term of the search.

        Returns:
            True for `person:` and `place:` terms, and words found in those columns.
        """
        if term.source is not None:
            return term.source in NARROWING
        probe = f"{_COLUMNS} : {term_expression(term)}"
        return self._connection.execute(sql.PROBE, (probe,)).fetchone() is not None

    def _keys(self, query: SearchQuery) -> tuple[int, ...] | None:
        """The rows of the files a search matches, best first.

        Args:
            query: Its words and filters.

        Returns:
            Them; None for a search without words nor filters (every file).
        """
        conditions, parameters = sql.conditions(query)
        if not conditions:
            return None
        where = sql.WHERE + sql.AND.join(conditions)
        if query.terms:
            statement = sql.KEYS + where + sql.BEST_FIRST
        else:
            statement = sql.FILE_KEYS + where
        rows = self._connection.execute(statement, parameters)
        return tuple(int(row[0]) for row in rows)
