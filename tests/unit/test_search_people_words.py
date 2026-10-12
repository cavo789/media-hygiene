"""The `person` words of the search: none without faces; unknown names explained."""

from __future__ import annotations

import sqlite3
from contextlib import closing

from media_hygiene.config.people_settings import PeopleSettings, Person
from media_hygiene.search.people_words import people_words, unknown_people
from media_hygiene.search.query import SearchQuery, parse_terms

NAMED = PeopleSettings(person=(Person(name="Mamie Jeanne", faces=("/a#0",)),))


def test_no_words_without_names_or_faces() -> None:
    """An index older than faces gives no word, and no error."""
    with closing(sqlite3.connect(":memory:")) as connection:
        assert people_words(connection, PeopleSettings()) == {}
        assert people_words(connection, NAMED) == {}


def test_unknown_names_are_said_in_one_line() -> None:
    """A word, a phrase or a start of a known name is fine, in any case and accent."""

    def said(text: str) -> str | None:
        return unknown_people(SearchQuery(parse_terms(text)), NAMED)

    for known in ("person:jeanne", 'person:"mamie jeanne"', "person:MAM*", "plage"):
        assert said(known) is None
    assert said("person:Chloé plage person:zo*") == (
        'Nobody is named "Chloé", "zo" yet: name their group on the \'people\' page '
        "first."
    )
