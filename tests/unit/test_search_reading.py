"""A sentence typed as a search, read as the index reads words (0345)."""

from __future__ import annotations

import sqlite3
from pathlib import Path

from media_hygiene.search import statements as sql
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.query import SearchQuery, Term, match_expression, parse_terms
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
    with _index() as index:
        return read_query(index, SearchQuery(parse_terms(text)))


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
    with _index() as index:
        read = read_query(index, typed)
    assert read == typed
    assert read_line(typed, read) is None


def _matches(text: str, stop: frozenset[str]) -> bool:
    """Whether a photo whose only mention is in the model's sentence is found."""
    columns_ = [source.value for source in TagSource]
    with _index() as index:
        index.stop_words = stop
        read = read_query(index, SearchQuery(parse_terms(text)))
        index.connection.execute(sql.CREATE)
        columns = ", ".join(columns_)
        values = ["" for _ in columns_]
        values[columns_.index(TagSource.CAPTION.value)] = (
            "un panneau de signalisation au bord"
        )
        marks = ", ".join("?" * len(values))
        index.connection.execute(
            f"INSERT INTO temp.{sql.TABLE} ({columns}) VALUES ({marks})",  # noqa: S608
            values,
        )
        expression = match_expression(read)
        found = index.connection.execute(
            f"SELECT count(*) FROM temp.{sql.TABLE} WHERE {sql.TABLE} MATCH ?",  # noqa: S608
            (expression,),
        ).fetchone()
    return bool(found[0])


def test_a_dropped_tag_is_not_found_through_the_caption() -> None:
    """Quoted, a dropped tag skips the sentence (0638); restored, found again."""
    typed = '"panneau de signalisation"'
    assert not _matches(typed, frozenset({"panneau de signalisation"}))
    assert _matches(typed, frozenset())
    read = _read(typed)
    assert read_line(SearchQuery(parse_terms(typed)), read) is None
