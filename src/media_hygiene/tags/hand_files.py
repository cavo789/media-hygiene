"""Read and save `[[tags.hand]]`: one file of photos per word typed by hand (0555).

Each word's photos are written to `tags/<word>.toml` as `{path, id}` lines
(`config.photo_ref`), atomically; then `config.toml` is edited with `tomlkit`, its
comments kept: each entry holds its `word` and `file`. A word left without photos
goes, and so does its file. Every caller reads its answer back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.config.hand_tags import FOLDER, KEY, SECTION, WORD, HandTag
from media_hygiene.config.photo_ref_files import (
    LinkedFile,
    LinkPlace,
    free_file,
    save_linked,
)
from media_hygiene.config.place_files import linked_entries
from media_hygiene.i18n import _
from media_hygiene.people.person_files import safe_name
from media_hygiene.places.toml_edit import loaded

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper

SUFFIX: Final = ".toml"


def read_hand_tags(config_file: Path) -> tuple[HandTag, ...]:
    """The words typed by hand and their photos, in the file's order.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        The entries.

    Raises:
        ValueError: The file, a linked file or an entry is invalid.
    """
    section = linked_entries(
        loaded(config_file).get(SECTION, {}), config_file.parent, KEY
    )
    rows = section.get(KEY, [])
    if not isinstance(rows, list):
        return ()
    return tuple(HandTag.model_validate(row) for row in rows)


def _file_of(entry: HandTag, taken: set[str]) -> str:
    """The file of a word's photos: the one written, else one after the word.

    Args:
        entry: The word's entry.
        taken: The files already given (case folded), completed here.

    Returns:
        The file, relative to the folder of `config.toml`.
    """
    return free_file(entry.file, f"{FOLDER}/{safe_name(entry.word)}", taken)


def save_hand_tags(config_file: Path, entries: tuple[HandTag, ...]) -> None:
    """Write every word's photos to its file, then link them from `config.toml`.

    Args:
        config_file: `config.toml`, created when missing.
        entries: Every entry, in order; those without photos are dropped.

    Raises:
        ValueError: A file leads out of the folder, or does not read back.
        OSError: A file cannot be written.
    """
    kept = [entry for entry in entries if entry.photos]
    taken = {entry.file.casefold() for entry in kept if entry.file}
    header = _("The photos you gave the word {word}; config.toml links this file.")
    linked = [
        LinkedFile(e.word, _file_of(e, taken), e.photos, header.format(word=e.word))
        for e in kept
    ]
    save_linked(config_file, LinkPlace(SECTION, KEY, WORD, FOLDER), linked)


def hand_words(
    config_file: Path, mapper: HostPathMapper
) -> dict[Path, tuple[str, ...]]:
    """The words typed by hand on each file, by container path.

    Args:
        config_file: `config.toml`; missing: none.
        mapper: Host paths to the container's.

    Returns:
        Each file with a word, its words in the file's order.

    Raises:
        ValueError: A file is not valid.
    """
    words: dict[Path, tuple[str, ...]] = {}
    for entry in read_hand_tags(config_file) if config_file.is_file() else ():
        for photo in entry.photos:
            path = mapper.to_container(photo.path)
            words[path] = (*words.get(path, ()), entry.word)
    return words
