"""The actions starred on the home page: `[home] favorites` of `config.toml` (0484).

The page sends the whole list, in its order; it is written with `tomlkit` (the user's
comments kept), parsed again, then replaces the file atomically, and the answer is the
list read back from the disk: never "saved" from memory. A name the catalog does not
know (a verb renamed or removed) is ignored when drawn, never an error.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import Array

from media_hygiene.places.toml_edit import ENCODING, document_of, loaded, table_of

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence
    from pathlib import Path

SECTION: Final = "home"
KEY: Final = "favorites"
# Shown, not saved, while the user starred nothing: the library, an import, an audit.
SUGGESTED: Final = ("search", "import", "audit")
MOST: Final = 24  # more stars than any menu holds: a list past it is refused


def read_favourites(config_file: Path) -> tuple[str, ...]:
    """The names written in the file, in their order.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        The names, each once; none when the key is missing or not a list of words.
    """
    try:
        value: object = loaded(config_file).get(SECTION, {}).get(KEY, [])
    except OSError, tomllib.TOMLDecodeError:
        return ()
    if not isinstance(value, list):
        return ()
    words = (name for name in value if isinstance(name, str))
    return tuple(dict.fromkeys(words))


def save_favourites(config_file: Path, names: Sequence[str]) -> tuple[str, ...]:
    """Write the list, keeping every comment, then read it back from the disk.

    Args:
        config_file: `config.toml`.
        names: The starred actions, in their order.

    Returns:
        The list the file now holds.
    """
    document = document_of(config_file)
    table_of(document, SECTION)[KEY] = _array(names)
    text = tomlkit.dumps(document)
    tomllib.loads(text)  # never write a file the next run cannot read
    temporary = config_file.with_name(f"{config_file.name}.tmp")
    temporary.write_text(text, ENCODING)
    temporary.replace(config_file)
    return read_favourites(config_file)


def _array(names: Sequence[str]) -> Array:
    """The names as a TOML array, each once.

    Args:
        names: The names, in their order.

    Returns:
        The array.
    """
    array = tomlkit.array()
    array.extend(dict.fromkeys(names))
    return array


def shown_favourites(saved: Sequence[str], known: Collection[str]) -> tuple[str, ...]:
    """The starred actions the page can draw: the unknown names left out.

    Args:
        saved: The names read from the file.
        known: The actions the page shows.

    Returns:
        The names kept, in their order.
    """
    return tuple(name for name in saved if name in known)
