"""The face lists of `[people]`, in files of their own under `/config/people/` (0300).

`config.toml` names each person with `file = "people/<name>.toml"`, and `[people]
ignored_file` the file of the ignored faces: the long lists (`faces`, `rejected`) live
there, one file per person, so that `config.toml` stays short and a change rewrites one
person only. Reading the settings puts the lists back in place: every reader sees
`faces` as before. Lists still written inline (before 0300, or by hand) are read too,
and added to those of the file.
"""

from __future__ import annotations

import functools
import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.people_parsed import parsed_file
from media_hygiene.config.stamped_text import stamped_value
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.config.layers import Layer

SECTION: Final = "people"
PERSON: Final = "person"
FILE: Final = "file"
FACES: Final = "faces"
REJECTED: Final = "rejected"
IGNORED: Final = "ignored"
IGNORED_FILE: Final = "ignored_file"
FOLDER: Final = "people"  # under the folder of config.toml
UNGUESSED: Final = "unguessed"  # faces no name is guessed for (2026-11-16)
UNGUESSED_PATH: Final = f"{FOLDER}/{UNGUESSED}.toml"  # never linked: always there
ENCODING: Final = "utf-8"


def linked_layer(layer: Layer, config_dir: Path) -> Layer:
    """The layer of `config.toml`, its `[people]` lists read from their files.

    Args:
        layer: The file's tables, as parsed.
        config_dir: The folder of `config.toml`.

    Returns:
        The layer, `[people]` filled in.

    Raises:
        ConfigError: A linked file is missing, outside the folder, or not TOML.
    """
    section = layer.get(SECTION)
    if section is None:
        return layer
    try:
        return {**layer, SECTION: linked_section(section, config_dir)}
    except ValueError as exc:
        message = _("The names of config.toml cannot be read: {error}.")
        raise ConfigError(message.format(error=exc)) from exc


def linked_section(
    section: Mapping[str, object], config_dir: Path
) -> dict[str, object]:
    """`[people]` as written, with the lists of its files read in.

    Args:
        section: The raw `[people]` table.
        config_dir: The folder of `config.toml`, the files' root.

    Returns:
        The table, each person's lists and the ignored faces filled from their files.

    Raises:
        ValueError: A file is missing, outside the folder, or not valid TOML.
    """
    resolved = dict(section)
    ignored_file = section.get(IGNORED_FILE)
    inline = section.get(IGNORED, [])
    if isinstance(ignored_file, str) and ignored_file and isinstance(inline, list):
        resolved[IGNORED] = [*inline, *read_lists(config_dir, ignored_file)[FACES]]
    if (config_dir / UNGUESSED_PATH).is_file():
        resolved[UNGUESSED] = read_lists(config_dir, UNGUESSED_PATH)[FACES]
    people = section.get(PERSON)
    if isinstance(people, list):
        resolved[PERSON] = [_person(entry, config_dir) for entry in people]
    return resolved


def _person(entry: object, config_dir: Path) -> object:
    """One `[[people.person]]` table, its lists read from its file.

    Args:
        entry: The raw table.
        config_dir: The folder of `config.toml`.

    Returns:
        The table with its lists; as it was without a file, its file missing (or
        malformed: the settings say what is wrong).
    """
    if not isinstance(entry, dict):
        return entry
    file = entry.get(FILE)
    faces, rejected = entry.get(FACES, []), entry.get(REJECTED, [])
    if not (isinstance(file, str) and file):
        return entry
    if not (isinstance(faces, list) and isinstance(rejected, list)):
        return entry
    if not linked_path(config_dir, file).is_file():  # gone: warned, tidy unlinks (0849)
        return entry
    lists = read_lists(config_dir, file)
    return {
        **entry,
        FACES: [*faces, *lists[FACES]],
        REJECTED: [*rejected, *lists[REJECTED]],
    }


def linked_path(config_dir: Path, relative: str) -> Path:
    """Where a linked file is, refused outside the folder of `config.toml`.

    Args:
        config_dir: The folder of `config.toml`.
        relative: The path written in it.

    Returns:
        The file.

    Raises:
        ValueError: The path leads out of the folder.
    """
    root = _resolved(config_dir)
    path = _resolved(root / relative)
    if not path.is_relative_to(root):
        message = _("{file} is not inside the folder of config.toml")
        raise ValueError(message.format(file=relative))
    return path


@functools.lru_cache(maxsize=4096)
def _resolved(path: Path) -> Path:
    """A path resolved once (2026-11-16).

    Each `resolve` inspects every folder on the way: a few hundred `lstat` per
    save, each one slow over Docker Desktop's file sharing.

    Args:
        path: The path.

    Returns:
        It, absolute, its links followed.
    """
    return path.resolve()


def read_lists(config_dir: Path, relative: str) -> dict[str, list[object]]:
    """The lists of a linked file.

    Args:
        config_dir: The folder of `config.toml`.
        relative: The path written in it.

    Returns:
        Its `faces` and `rejected` (empty when absent), the tables of 0570 as keys.

    Raises:
        ValueError: The file is missing, outside the folder, or not valid TOML.
    """
    missing = _(
        "{file} is missing: restore it, or remove the line file = '{file}' "
        "of config.toml (its faces are then forgotten)"
    )
    path = linked_path(config_dir, relative)
    load_linked(path, relative, missing)  # says what is wrong with the file
    return {key: list(keys) for key, keys in parsed_file(path).lists.items()}


def load_linked(path: Path, relative: str, missing: str) -> dict[str, object]:
    """Read a TOML file linked from `config.toml`.

    Args:
        path: The resolved file.
        relative: The path written in `config.toml`, for the messages.
        missing: The message when the file is missing (`{file}` placeholder).

    Returns:
        Its tables and keys.

    Raises:
        ValueError: The file is missing or not valid TOML.
    """
    try:
        return stamped_value(path, tomllib.loads)
    except FileNotFoundError:
        raise ValueError(missing.format(file=relative)) from None
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        message = _("{file} is not valid TOML: {error}")
        raise ValueError(message.format(file=relative, error=exc)) from exc
