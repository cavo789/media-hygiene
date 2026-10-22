"""The face lists of `[people]`, in files of their own under `/config/people/` (0300).

`config.toml` names each person with `file = "people/<name>.toml"`, and `[people]
ignored_file` the file of the ignored faces: the long lists (`faces`, `rejected`) live
there, one file per person, so that `config.toml` stays short and a change rewrites one
person only. Reading the settings puts the lists back in place: every reader sees
`faces` as before. Lists still written inline (before 0300, or by hand) are read too,
and added to those of the file.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

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
        The table with its lists; as it was without a file (or malformed: the
        settings say what is wrong).
    """
    if not isinstance(entry, dict):
        return entry
    file = entry.get(FILE)
    faces, rejected = entry.get(FACES, []), entry.get(REJECTED, [])
    if not (isinstance(file, str) and file):
        return entry
    if not (isinstance(faces, list) and isinstance(rejected, list)):
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
    root = config_dir.resolve()
    path = (root / relative).resolve()
    if not path.is_relative_to(root):
        message = _("{file} is not inside the folder of config.toml")
        raise ValueError(message.format(file=relative))
    return path


def read_lists(config_dir: Path, relative: str) -> dict[str, list[object]]:
    """The lists of a linked file.

    Args:
        config_dir: The folder of `config.toml`.
        relative: The path written in it.

    Returns:
        Its `faces` and `rejected` (empty when absent).

    Raises:
        ValueError: The file is missing, outside the folder, or not valid TOML.
    """
    path = linked_path(config_dir, relative)
    try:
        loaded = tomllib.loads(path.read_text(ENCODING))
    except FileNotFoundError:
        message = _(
            "{file} is missing: restore it, or remove the line file = '{file}' "
            "of config.toml (its faces are then forgotten)"
        )
        raise ValueError(message.format(file=relative)) from None
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        message = _("{file} is not valid TOML: {error}")
        raise ValueError(message.format(file=relative, error=exc)) from exc
    lists: dict[str, list[object]] = {}
    for key in (FACES, REJECTED):
        value = loaded.get(key, [])
        lists[key] = value if isinstance(value, list) else [value]
    return lists
