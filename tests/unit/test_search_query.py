"""What the user types, made into FTS5: words, phrases, prefixes, sources."""

from __future__ import annotations

from media_hygiene.search.query import (
    Filters,
    SearchQuery,
    Term,
    match_expression,
    parse_terms,
)
from media_hygiene.tags.models import TagSource


def test_words_phrases_prefixes_and_sources() -> None:
    """Each kind of token is read; an unclosed quote runs to the end."""
    terms = parse_terms('Durbuy "bord de mer" anniv* place:Liège VISION:"chat" "neige')
    assert terms == (
        Term("Durbuy"),
        Term("bord de mer", phrase=True),
        Term("anniv", prefix=True),
        Term("Liège", TagSource.PLACE),
        Term("chat", TagSource.VISION, phrase=True),
        Term("neige", phrase=True),
    )


def test_unknown_names_and_punctuation() -> None:
    """`http:` is no source; a token without a letter is left out."""
    assert parse_terms("note:x - * ''") == (Term("note:x"),)
    assert not parse_terms("   ")


def test_expression_quotes_everything_and_adds_singulars() -> None:
    """Quotes are doubled, plurals also match their singular, prefixes keep `*`."""
    query = SearchQuery(parse_terms('fleurs anniv* place:durbuy "fleurs bleues"'))
    assert match_expression(query) == (
        '("fleurs" OR "fleur") AND "anniv"* AND place : "durbuy" AND "fleurs bleues"'
    )
    quoted = SearchQuery((Term('a"b', phrase=True),))
    assert match_expression(quoted) == '"a""b"'


def test_both_languages_singulars() -> None:
    """A word is made singular the French and the English way: either may match."""
    query = SearchQuery(parse_terms("parties"))
    assert match_expression(query) == '("parties" OR "party" OR "partie")'


def test_a_source_filter_wraps_every_word() -> None:
    """The page's source filter applies to the whole search; no word, no MATCH."""
    query = SearchQuery(parse_terms("chat"), Filters(source=TagSource.CAPTION))
    assert match_expression(query) == 'caption : ("chat")'
    assert match_expression(SearchQuery(())) is None
