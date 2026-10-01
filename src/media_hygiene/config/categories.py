"""Extension categories: names for lists of extensions (`photo`, `video`, `documents`).

A category is only a name: what happens to a file (decoded, deleted or quarantined)
still follows its extension. The built-in categories come from the extension
constants and cannot be redefined; `[scan.categories]` adds the user's own.
"""

from __future__ import annotations

import difflib
import re
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.config.extensions import (
    check_extensions,
    normalized_extensions,
    split_values,
)
from media_hygiene.constants import (
    IMAGE_EXTENSIONS,
    MEDIA_EXTENSIONS,
    RAW_EXTENSIONS,
    VIDEO_EXTENSIONS,
)

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping

type Categories = Mapping[str, tuple[str, ...]]

BUILTIN_CATEGORIES: Final[Categories] = MappingProxyType(
    {
        name: tuple(sorted(extensions))
        for name, extensions in (
            ("photo", IMAGE_EXTENSIONS),
            ("raw", RAW_EXTENSIONS),
            ("video", VIDEO_EXTENSIONS),
            ("media", MEDIA_EXTENSIONS),
        )
    }
)
_DOT: Final = "."
_CATEGORY_NAME: Final = re.compile(r"[a-z0-9_-]+")
# `photos` is a typo of `photo`; `raf` or `rar` (0.67 from `raw`) are extensions.
_TYPO_CUTOFF: Final = 0.8


def valid_categories(
    categories: Mapping[str, Iterable[str]],
) -> dict[str, tuple[str, ...]]:
    """Validate `[scan.categories]`: names, then their extensions.

    Args:
        categories: The user's categories, as configured.

    Returns:
        Lowercase names, each with its normalised extensions.

    Raises:
        ValueError: A name is malformed, built in or an extension; a category is
            empty, lists another category or a sidecar.
    """
    valid: dict[str, tuple[str, ...]] = {}
    for raw_name, values in categories.items():
        name = raw_name.strip().casefold()
        _check_name(name)
        names = {*BUILTIN_CATEGORIES, *(key.strip().casefold() for key in categories)}
        nested = [value for value in split_values(values) if value in names]
        if nested:
            message = (
                f"category {name}: a category lists extensions, not categories; "
                f"for the extension, write .{nested[0]}"
            )
            raise ValueError(message)
        extensions = normalized_extensions(values)
        if not extensions:
            message = f"category {name} lists no extension, e.g. {name} = ['pdf']"
            raise ValueError(message)
        valid[name] = extensions
    return valid


def _check_name(name: str) -> None:
    """Refuse a malformed category name, a built-in one or a media extension.

    Args:
        name: A lowercase category name.

    Raises:
        ValueError: The name cannot be a user category.
    """
    if not _CATEGORY_NAME.fullmatch(name):
        message = (
            f"invalid category name {name!r}: letters, digits, '-' and '_' only, "
            "such as documents"
        )
        raise ValueError(message)
    if name in BUILTIN_CATEGORIES:
        message = (
            f"{name} is a built-in category, it cannot be redefined: choose another "
            f"name, e.g. my_{name}"
        )
        raise ValueError(message)
    if _DOT + name in MEDIA_EXTENSIONS:
        message = f"{name} is an extension: choose another name for the category"
        raise ValueError(message)


def requested(values: Iterable[str], categories: Categories) -> tuple[str, ...]:
    """Tell categories from extensions in `--ext` / `extensions`.

    A value with a dot is an extension; without one, it is a category when that
    name exists, otherwise an extension (`pdf`).

    Args:
        values: As typed, comma-separated or not.
        categories: The user's categories (the built-in ones are always known).

    Returns:
        Category names as they are, extensions with their dot, without duplicates.

    Raises:
        ValueError: A value is malformed, a sidecar, or close to a category name.
    """
    known = [*BUILTIN_CATEGORIES, *categories]
    items: list[str] = []
    for value in split_values(values):
        if value.startswith(_DOT) or value not in known:
            items.append(_DOT + value.lstrip(_DOT))
            _check_typo(value, known)
        else:
            items.append(value)
    unique = tuple(dict.fromkeys(items))
    check_extensions([item for item in unique if item.startswith(_DOT)])
    return unique


def _check_typo(value: str, known: list[str]) -> None:
    """Refuse a dotless value that looks like a misspelt category (`photos`).

    Args:
        value: A value that is not a category name.
        known: Every category name.

    Raises:
        ValueError: The value is close to a category name.
    """
    if value.startswith(_DOT) or _DOT + value in MEDIA_EXTENSIONS:
        return
    close = difflib.get_close_matches(value, known, n=1, cutoff=_TYPO_CUTOFF)
    if close:
        message = (
            f"{value}: unknown category, did you mean {close[0]}? For the "
            f"extension, write .{value}"
        )
        raise ValueError(message)


def expanded(items: Iterable[str], categories: Categories) -> tuple[str, ...]:
    """Turn requested categories and extensions into extensions.

    Args:
        items: Validated requests (see `requested`).
        categories: The user's categories.

    Returns:
        The extensions, in the requested order, without duplicates.
    """
    every = {**BUILTIN_CATEGORIES, **categories}
    extensions = (
        extension for item in items for extension in (every.get(item) or (item,))
    )
    return tuple(dict.fromkeys(extensions))
