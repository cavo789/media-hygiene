"""*Path contains* (0426): a part of the path, wildcards, or a regex in slashes.

Three forms, told apart by what is typed, so an ordinary path never becomes a pattern:
`/…/` is a regular expression (case-insensitive, searched anywhere in the path); a
text with `*` (any characters) or `?` (one character) is a wildcard pattern, matched
anywhere in the path; any other text is a plain part of the path.
"""

from __future__ import annotations

import re
from functools import lru_cache
from typing import Final

from media_hygiene.i18n import _

REGEX: Final = "mh_regex"  # the SQL function registered on the connection
_SLASH: Final = "/"
_ESCAPE: Final = "\\"
_WILD: Final = frozenset("*?")
_LIKE_SPECIAL: Final = {"%": "\\%", "_": "\\_", "\\": "\\\\", "*": "%", "?": "_"}
_LITERAL: Final = "instr(fold(files.path), ?) > 0"
_WILDCARD: Final = f"fold(files.path) LIKE ? ESCAPE '{_ESCAPE}'"
_REGEXP: Final = f"{REGEX}(?, files.path)"
_SHORTEST_REGEX: Final = 3  # `/x/`


def regex_of(typed: str) -> str | None:
    """The regular expression a text is written as, if it is one.

    Args:
        typed: What the field holds.

    Returns:
        The pattern between the slashes; None for any other text.
    """
    text = typed.strip()
    if (
        len(text) >= _SHORTEST_REGEX
        and text.startswith(_SLASH)
        and text.endswith(_SLASH)
    ):
        return text[1:-1]
    return None


def refusal(typed: str) -> str | None:
    """Say why a typed regular expression cannot be used.

    Args:
        typed: What the field holds.

    Returns:
        A one-line message for an invalid regex; None for everything else.
    """
    pattern = regex_of(typed)
    if pattern is None:
        return None
    try:
        re.compile(pattern)
    except re.error as error:
        return _("Path contains: invalid regular expression ({error}).").format(
            error=error
        )
    return None


@lru_cache(maxsize=32)
def _compiled(pattern: str) -> re.Pattern[str] | None:
    try:
        return re.compile(pattern, re.IGNORECASE)
    except re.error:
        return None


def regex_matches(pattern: str, path: str) -> int:
    """Tell whether a path matches a regex (the SQL function).

    An invalid pattern matches nothing.

    Args:
        pattern: The regular expression, case-insensitive.
        path: The path of the file.

    Returns:
        1 when the pattern is found in the path, else 0.
    """
    compiled = _compiled(pattern)
    return int(compiled is not None and compiled.search(path) is not None)


def condition(typed: str) -> tuple[str, str] | None:
    """The SQL condition of the field, and its parameter.

    Args:
        typed: What the field holds.

    Returns:
        A constant SQL fragment and the value to bind; None for an empty field.
    """
    pattern = regex_of(typed)
    if pattern is not None:
        return _REGEXP, pattern
    folder = typed.strip().replace("\\", "/").casefold()
    if not folder:
        return None
    if _WILD.isdisjoint(folder):
        return _LITERAL, folder
    like = "".join(_LIKE_SPECIAL.get(char, char) for char in folder)
    return _WILDCARD, f"%{like}%"
