"""What the user typed, made into an FTS5 query: words, phrases, prefixes, sources.

`Durbuy ours` finds the files with both words, from any source; `"bord de mer"` the
phrase; `anniv*` every word starting so; `place:durbuy` the word among the places only.
Each word is quoted for FTS5, so that nothing the user types is read as its syntax. A
word also matches its singular (`bougies` → `bougie`), the form tags are kept in; the
index folds case and accents (`noel` finds `Noël`).
"""

from __future__ import annotations

import re
from dataclasses import dataclass, field
from typing import Final

from media_hygiene.constants import Locale
from media_hygiene.tags.models import TagSource
from media_hygiene.tags.plurals import singular

_TOKEN: Final = re.compile(
    r'(?:(?P<source>\w+):)?(?:"(?P<phrase>[^"]*)"?|(?P<word>[^\s"]+))'
)
_PREFIX: Final = "*"
_QUOTE: Final = '"'
_AND: Final = " AND "
_OR: Final = " OR "
_SAYS_SOMETHING: Final = re.compile(r"\w")


@dataclass(frozen=True, slots=True)
class Term:
    """One word or phrase to find; `source` limits it to one source of tags."""

    text: str
    source: TagSource | None = None
    prefix: bool = False
    phrase: bool = False


@dataclass(frozen=True, slots=True)
class Filters:
    """What narrows a search beyond its words: years, a folder, one source."""

    years: tuple[int, int] | None = None  # first and last year, both included
    folder: str = ""  # a part of the path, any case
    source: TagSource | None = None  # every word among this source only


@dataclass(frozen=True, slots=True)
class SearchQuery:
    """The words of a search and its filters."""

    terms: tuple[Term, ...]
    filters: Filters = field(default_factory=Filters)


def parse_terms(text: str) -> tuple[Term, ...]:
    """Read the words, phrases, prefixes and sources of a search.

    Never fails: an unknown `name:` stays part of the word, an unclosed quote runs to
    the end, and a token without any letter or digit is left out.

    Args:
        text: What the user typed.

    Returns:
        The terms, in order.
    """
    terms: list[Term] = []
    for match in _TOKEN.finditer(text):
        named, phrase, word = match.group("source", "phrase", "word")
        source = TagSource(named.casefold()) if _is_source(named) else None
        if named and source is None:
            word = f"{named}:{phrase if phrase is not None else word}"
            phrase = None
        if phrase is not None:
            term = Term(phrase.strip(), source, phrase=True)
        else:
            stem = word.rstrip(_PREFIX)
            term = Term(stem, source, prefix=stem != word)
        if _SAYS_SOMETHING.search(term.text):
            terms.append(term)
    return tuple(terms)


def match_expression(query: SearchQuery) -> str | None:
    """Write the FTS5 `MATCH` expression of a search.

    Args:
        query: Its words and filters.

    Returns:
        The expression; None without any word (the filters alone then apply).
    """
    if not query.terms:
        return None
    joined = _AND.join(term_expression(term) for term in query.terms)
    source = query.filters.source
    return joined if source is None else f"{source.value} : ({joined})"


def _is_source(name: str | None) -> bool:
    """Tell whether `name:` names a source of tags.

    Args:
        name: The text before the colon, if any.

    Returns:
        True for `vision`, `place`, …, in any case.
    """
    return name is not None and name.casefold() in set(TagSource)


def term_expression(term: Term) -> str:
    """Write one term: quoted, its singulars as alternatives, its source first.

    Args:
        term: The term.

    Returns:
        Its FTS5 expression.
    """
    forms = [term.text]
    if not term.phrase:
        folded = term.text.casefold()
        forms += [singular(folded, language) for language in Locale]
    suffix = _PREFIX if term.prefix else ""
    quoted = [
        f"{_QUOTE}{form.replace(_QUOTE, _QUOTE * 2)}{_QUOTE}{suffix}"
        for form in dict.fromkeys(forms)
    ]
    inner = quoted[0] if len(quoted) == 1 else f"({_OR.join(quoted)})"
    return inner if term.source is None else f"{term.source.value} : {inner}"
