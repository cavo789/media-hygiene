"""Check the regular expressions a user writes in `config.toml`."""

from __future__ import annotations

import re


def valid_patterns(patterns: tuple[str, ...]) -> tuple[str, ...]:
    """Reject patterns that are not valid regular expressions.

    Args:
        patterns: Configured patterns.

    Returns:
        The patterns, unchanged.

    Raises:
        ValueError: A pattern does not compile.
    """
    for pattern in patterns:
        try:
            re.compile(pattern)
        except re.error as exc:
            message = f"{pattern!r} is not a valid regular expression: {exc}"
            raise ValueError(message) from exc
    return patterns
