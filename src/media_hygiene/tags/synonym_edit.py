"""Add a synonym to `[tags] synonyms`, or take it out, in `config.toml` (0622).

`panneau = "panneau de signalisation"`: the next `tags` names the word so. One entry per
word whatever its case; a merge again replaces the tag it means. Every caller reads its
answer back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import tomlkit

from media_hygiene.places.toml_edit import (
    document_of,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from pathlib import Path

_SECTION: Final = "tags"
_KEY: Final = "synonyms"


def saved_synonyms(config_file: Path) -> dict[str, str]:
    """The synonyms the next run reads.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        Each word and the tag it means.

    Raises:
        ValueError: The file is not TOML.
    """
    written: object = loaded(config_file).get(_SECTION, {}).get(_KEY, {})
    if not isinstance(written, dict):
        return {}
    return {str(word): str(tag) for word, tag in written.items()}


def add_synonym(config_file: Path, word: str, target: str) -> None:
    """Name a word as another tag from now on.

    Args:
        config_file: `config.toml`, created when missing.
        word: The synonym.
        target: The tag it means.

    Raises:
        ValueError: The file is not TOML, or `[tags]` is not a table.
        OSError: The file cannot be written.
    """
    _write(config_file, word, target)


def remove_synonym(config_file: Path, word: str) -> None:
    """Take a word out of the synonyms; not there, nothing changes.

    Args:
        config_file: `config.toml`.
        word: The word, any case.

    Raises:
        ValueError: The file is not TOML, or `[tags]` is not a table.
        OSError: The file cannot be written.
    """
    folded = word.casefold()
    if any(each.casefold() == folded for each in saved_synonyms(config_file)):
        _write(config_file, word, "")


def _write(config_file: Path, word: str, target: str) -> None:
    """Replace the entry of a word (empty target: remove it); empty, the key goes.

    Args:
        config_file: `config.toml`.
        word: The word.
        target: The tag it means; empty to remove.
    """
    document = document_of(config_file)
    table = table_of(document, _SECTION)
    folded = word.casefold()
    entries = {
        each: tag
        for each, tag in saved_synonyms(config_file).items()
        if each.casefold() != folded
    }
    if target:
        entries[word] = target
    if entries:
        inline = tomlkit.inline_table()
        inline.update(entries)
        table[_KEY] = inline
    else:
        table.pop(_KEY, None)
    write_document(config_file, document)
