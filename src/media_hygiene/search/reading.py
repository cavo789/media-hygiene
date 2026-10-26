"""A sentence typed as a search, read as the index reads words (0345).

`Papy dans le jardin`: the index never keeps `dans` nor `le` (stop words of `[tags]`,
words of one or two letters, `tags/normalize.py`), so a search keeping them finds
nothing. The query drops them the same way (a number stays: `snow 2008`), and a word
that is the name of someone on a photo is looked for among the people: the sentence
means `person:papy jardin`. A phrase in quotes, a `source:` word and a prefix (`anniv*`)
are kept as typed. Every reader of a search reads it so (the page, *Pick all N found*,
the albums, the table of the command line): the same words, the same files.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.people.folding import folded
from media_hygiene.search import statements as sql
from media_hygiene.search.people_words import unknown_people
from media_hygiene.tags.models import TagSource

if TYPE_CHECKING:
    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.search.query import SearchQuery, Term

_SHORTEST: Final = 3  # as the index keeps a word (`normalize._MIN_LENGTH`)
_NAMES: Final = f"SELECT DISTINCT value FROM temp.{sql.PEOPLE}"  # noqa: S608


def read_query(index: SearchIndex, query: SearchQuery) -> SearchQuery:
    """The search as the index can answer it: little words out, names among the people.

    Args:
        index: The open index: its stop words, the names on its photos.
        query: The search as typed.

    Returns:
        The search read; as typed when nothing changes or every word would go.
    """
    names = frozenset(
        word
        for (value,) in index.connection.execute(_NAMES)
        for word in folded(str(value)).split()
    )
    terms = tuple(
        read
        for term in query.terms
        if (read := _read(term, (index.stop_words, names))) is not None
    )
    return replace(query, terms=terms) if terms else query


def read_line(typed: SearchQuery, read: SearchQuery) -> str | None:
    """Say how a sentence was read, when it was not read as typed.

    Args:
        typed: The search as typed.
        read: The search read.

    Returns:
        E.g. `Read as: Papy (person) + jardin`; None when read as typed.
    """
    if read.terms == typed.terms:
        return None
    person = _("person")
    words = [
        f"{term.text} ({person})" if term.source is TagSource.PERSON else term.text
        for term in read.terms
    ]
    return _("Read as: {words}.").format(words=" + ".join(words))


def _read(term: Term, known: tuple[frozenset[str], frozenset[str]]) -> Term | None:
    """One word of a search, read.

    Args:
        term: The word.
        known: The stop words (folded), the words of the people's names (folded).

    Returns:
        The word, among the people when it is a name; None for a little word.
    """
    if term.phrase or term.source is not None or term.prefix:
        return term
    stop, names = known
    text = term.text
    if not text.isdigit() and (len(text) < _SHORTEST or text.casefold() in stop):
        return None
    if folded(text) in names:
        return replace(term, source=TagSource.PERSON)
    return term


def search_note(
    typed: SearchQuery, read: SearchQuery, people: PeopleSettings
) -> str | None:
    """The line under a search: how it was read, else the names that name nobody.

    Args:
        typed: The search as typed.
        read: The search read.
        people: `[people]`, with the names.

    Returns:
        The line, or None.
    """
    return read_line(typed, read) or unknown_people(read, people)
