"""Extensions as `--ext` and `[scan]` take them: split, normalised, checked."""

from __future__ import annotations

import re
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import SIDECAR_EXTENSIONS

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence

_DOT: Final = "."
_EXTENSION: Final = re.compile(r"\.[\w-]+")


def split_values(values: Iterable[str]) -> list[str]:
    """Split comma-separated values, trim them, ignore case, drop empty ones.

    Args:
        values: As typed, e.g. `["PNG", ".webp,png"]`.

    Returns:
        E.g. `["png", ".webp", "png"]`.
    """
    parts = (part.strip().casefold() for item in values for part in item.split(","))
    return [part for part in parts if part]


def normalized_extensions(values: Iterable[str]) -> tuple[str, ...]:
    """Normalise `PNG`, `png` or `.png` to `.png` and reject invalid ones.

    Args:
        values: Extensions, with or without their dot, comma-separated or not.

    Returns:
        The lowercase extensions with their dot, without duplicates.

    Raises:
        ValueError: An extension is malformed or is a sidecar's.
    """
    normalized = tuple(
        dict.fromkeys(_DOT + value.lstrip(_DOT) for value in split_values(values))
    )
    check_extensions(normalized)
    return normalized


def check_extensions(extensions: Sequence[str]) -> None:
    """Refuse malformed extensions and sidecars.

    Args:
        extensions: Extensions with their dot.

    Raises:
        ValueError: An extension is malformed or is a sidecar's.
    """
    malformed = [ext for ext in extensions if not _EXTENSION.fullmatch(ext)]
    if malformed:
        message = (
            f"invalid extension {', '.join(malformed)}: letters, digits, '-' and "
            "'_' only, such as pdf"
        )
        raise ValueError(message)
    sidecars = [ext for ext in extensions if ext in SIDECAR_EXTENSIONS]
    if sidecars:
        message = (
            f"{', '.join(sidecars)}: sidecars follow the photo of the same name, "
            "they are not analysed on their own"
        )
        raise ValueError(message)
