"""Recognise file names that look like copies: `IMG (1).jpg`, `IMG - Copie.jpg`, ..."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.name_patterns import GENERATED_NAMES

if TYPE_CHECKING:
    from pathlib import Path

_COPY_WORDS: Final = "copy|copie|kopie|copia|kopia|kopio"
_COPY_PATTERNS: Final = (
    # A small counter between brackets at the end, as Windows names a second copy
    # (a year such as `Vacances (2019)` is part of the name).
    re.compile(r"\(\d{1,2}\)$"),
    # Matches: IMG - Copy / IMG_copie / IMG copy 2
    re.compile(rf"[\s_-]+({_COPY_WORDS})(\s*\d+)?$", re.IGNORECASE),
    # Matches: Copy of IMG / Copie de IMG / Kopie van IMG
    re.compile(rf"^({_COPY_WORDS})\s+(of|de|van|di|von)\s", re.IGNORECASE),
)
# macOS Finder names a duplicate `<name> 2`: a copy only for a device-generated name.
_FINDER_COPY: Final = re.compile(r"^(?P<base>.+) \d{1,2}$")
_GENERATED: Final = tuple(re.compile(p, re.IGNORECASE) for p in GENERATED_NAMES)


def _finder_base(stem: str) -> str | None:
    """Return the name before a Finder counter, or None when there is none."""
    match = _FINDER_COPY.match(stem)
    if match is None:
        return None
    base = match.group("base")
    return base if any(p.fullmatch(base) for p in _GENERATED) else None


def looks_like_copy(path: Path) -> bool:
    """Tell whether the file name follows a usual "copy" naming pattern.

    Args:
        path: File to test.

    Returns:
        True when the name (without extension) looks like a copy.
    """
    stem = path.stem.strip()
    if any(pattern.search(stem) for pattern in _COPY_PATTERNS):
        return True
    return _finder_base(stem) is not None


def without_copy_marks(stem: str) -> str:
    """Remove the "copy" marks from a file name, to judge the name itself.

    Args:
        stem: A file name without its extension, e.g. `Copie de IMG_0001 (2)`.

    Returns:
        The name without its copy marks, e.g. `IMG_0001`.
    """
    name = stem.strip()
    for pattern in _COPY_PATTERNS:
        name = pattern.sub("", name).strip()
    return _finder_base(name) or name
