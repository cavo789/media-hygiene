"""Names compared without case nor accents: `liege` finds Liège.

Town names are also compared without their separators: `Saint-Jean de Luz` is
GeoNames' Saint-Jean-de-Luz (`town_key`).
"""

from __future__ import annotations

import re
import unicodedata
from typing import Final

# Hyphens, apostrophes (straight and typographic), underscores and dots: a space.
_SEPARATORS: Final = re.compile(r"[\s\-\u2010-\u2015'\u2019\u02bc_.]+")


def fold(text: str) -> str:
    """A text without case nor accents, to compare names.

    Args:
        text: A name.

    Returns:
        It, folded: `Liège` → `liege`.
    """
    decomposed = unicodedata.normalize("NFKD", text.strip().casefold())
    return "".join(char for char in decomposed if not unicodedata.combining(char))


def town_key(text: str) -> str:
    """A town name folded, its separators read as one space, to compare names.

    Args:
        text: A town name, a folder name, or what the user typed.

    Returns:
        It, folded: `Saint-Jean de Luz` and `saint_jean_de_luz` → `saint jean de luz`.
    """
    return _SEPARATORS.sub(" ", fold(text)).strip()
