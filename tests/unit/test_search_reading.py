"""A sentence typed as a search, read as the index reads words (0345)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import SearchQuery, Term, parse_terms
from media_hygiene.search.reading import read_line, read_query
from media_hygiene.tags.models import TagSource


def _index() -> SearchIndex:
    """An index in memory, Papy named on a photo, French stop words."""
    index = SearchIndex(sqlite3.connect(":memory:"))
    index.name_people({Path("/data/c/a.jpg"): ("Papy",)})
    index.stop_words = frozenset({"dans", "avec"})
    return index


def _read(text: str) -> SearchQuery:
    """Read a search typed."""
    return read_query(_index(), SearchQuery(parse_terms(text)))


def test_a_sentence_is_a_person_and_words() -> None:
    """`Papy dans le jardin` is `person:papy jardin`."""
    read = _read("Papy dans le jardin")
    assert read.terms == (Term("Papy", TagSource.PERSON), Term("jardin"))
    typed = SearchQuery(parse_terms("Papy dans le jardin"))
    assert read_line(typed, read) == "Read as: Papy (person) + jardin."


def test_a_phrase_a_source_a_prefix_and_a_year_are_kept() -> None:
    """Quotes, `place:`, `anniv*` and `2008` stay as typed."""
    read = _read('"dans le jardin" place:le anniv* neige 2008')
    assert [term.text for term in read.terms] == [
        "dans le jardin",
        "le",
        "anniv",
        "neige",
        "2008",
    ]


def test_only_little_words_are_left_as_typed() -> None:
    """Nothing to drop to: the search is read as typed, and nothing is said."""
    typed = SearchQuery(parse_terms("le la"))
    read = read_query(_index(), typed)
    assert read == typed
    assert read_line(typed, read) is None
