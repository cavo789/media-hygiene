"""Add a word to `[tags] stop_words`, or take it out, in `config.toml` (0546).

`stop_words`, once written, replaces the built-in list: the first word dropped writes
the whole list, the word after it. The words not built in are the words dropped; a
list back to the built-in one leaves the file, so a later version's list applies again.
Every caller reads its answer back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import tomlkit

from media_hygiene.config.tags_settings import STOP_WORDS
from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from pathlib import Path

_SECTION: Final = "tags"
_KEY: Final = "stop_words"


def saved_stop_words(config_file: Path) -> tuple[str, ...]:
    """The stop words the next run reads.

    Args:
        config_file: `config.toml`; missing: the built-in list.

    Returns:
        The list written, else the built-in one.

    Raises:
        ValueError: The file is not TOML.
    """
    written = loaded(config_file).get(_SECTION, {}).get(_KEY)
    return STOP_WORDS if written is None else tuple(str(word) for word in written)


def dropped_words(config_file: Path) -> tuple[str, ...]:
    """The words dropped: the stop words that are not built in.

    Args:
        config_file: `config.toml`.

    Returns:
        Them, sorted.

    Raises:
        ValueError: The file is not TOML.
    """
    built_in = {word.casefold() for word in STOP_WORDS}
    return tuple(
        sorted(
            (w for w in saved_stop_words(config_file) if w.casefold() not in built_in),
            key=str.casefold,
        )
    )


def add_stop_word(config_file: Path, word: str) -> None:
    """Add a word to the stop words; there already, nothing changes.

    Args:
        config_file: `config.toml`, created when missing.
        word: The word.

    Raises:
        ValueError: The file is not TOML, or `[tags]` is not a table.
        OSError: The file cannot be written.
    """
    words = saved_stop_words(config_file)
    if word.casefold() not in {each.casefold() for each in words}:
        _write(config_file, (*words, word))


def remove_stop_word(config_file: Path, word: str) -> None:
    """Take a word out of the stop words.

    Args:
        config_file: `config.toml`.
        word: The word, any case.

    Raises:
        ValueError: The file is not TOML, or `[tags]` is not a table.
        OSError: The file cannot be written.
    """
    folded = word.casefold()
    words = saved_stop_words(config_file)
    _write(config_file, tuple(each for each in words if each.casefold() != folded))


def _write(config_file: Path, words: tuple[str, ...]) -> None:
    """Replace the list; back to the built-in one, the key goes.

    Args:
        config_file: `config.toml`.
        words: The list.
    """
    document = document_of(config_file)
    table = table_of(document, _SECTION)
    if words == STOP_WORDS:
        table.pop(_KEY, None)
    else:
        table[_KEY] = tomlkit.array().multiline(multiline=True)
        table[_KEY].extend(words)
    write_document(config_file, document)
