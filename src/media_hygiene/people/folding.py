"""Names compared without case nor accents: `Chloé`, `chloe` and `CHLOE` are one."""

from __future__ import annotations

import unicodedata
from typing import Final

_COMBINING: Final = "Mn"  # the accents, once a letter is decomposed
_DECOMPOSED: Final = "NFKD"


def folded(text: str) -> str:
    """A name without case nor accents, as `search` and `classify` compare them.

    Args:
        text: The name.

    Returns:
        `Chloé` → `chloe`.
    """
    decomposed = unicodedata.normalize(_DECOMPOSED, text.strip().casefold())
    return "".join(c for c in decomposed if unicodedata.category(c) != _COMBINING)
