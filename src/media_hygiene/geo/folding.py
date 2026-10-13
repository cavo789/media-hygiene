"""Names compared without case nor accents: `liege` finds Liège."""

from __future__ import annotations

import unicodedata


def fold(text: str) -> str:
    """A text without case nor accents, to compare names.

    Args:
        text: A name.

    Returns:
        It, folded: `Liège` → `liege`.
    """
    decomposed = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))
