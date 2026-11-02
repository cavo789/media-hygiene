"""The photos of `[[classify.place_photos]]`, one file per place in `/config/places/`.

`config.toml` keeps each place's entry short: its name and `file =
"places/<name>.toml"`, which lists the photos as `{path, id}` (`config.photo_ref`,
0551). Reading the settings puts the photos back in place. Photos still written
inline (before 0551, as `sha256` + `size`) are read too, added to those of the file;
the next save moves them to the file.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.people_files import ENCODING, linked_path
from media_hygiene.errors import ConfigError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.config.layers import Layer

SECTION: Final = "classify"
KEY: Final = "place_photos"
FILE: Final = "file"
PHOTOS: Final = "photos"
FOLDER: Final = "places"  # under the folder of config.toml


def linked_places(layer: Layer, config_dir: Path) -> Layer:
    """The layer of `config.toml`, the photos of each place read from its file.

    Args:
        layer: The file's tables, as parsed.
        config_dir: The folder of `config.toml`.

    Returns:
        The layer, `[[classify.place_photos]]` filled in.

    Raises:
        ConfigError: A linked file is missing, outside the folder, or not TOML.
    """
    section = layer.get(SECTION)
    if section is None:
        return layer
    try:
        return {**layer, SECTION: linked_entries(section, config_dir)}
    except ValueError as exc:
        message = _("The places of config.toml cannot be read: {error}.")
        raise ConfigError(message.format(error=exc)) from exc


def linked_entries(
    section: Mapping[str, object], config_dir: Path, key: str = KEY
) -> dict[str, object]:
    """`[classify]` as written, each place's photos read from its file.

    Args:
        section: The raw `[classify]` table.
        config_dir: The folder of `config.toml`.
        key: The array of entries: the places', or `[[tags.hand]]` (0555).

    Returns:
        The table, the photos filled in.

    Raises:
        ValueError: A file is missing, outside the folder, or not valid TOML.
    """
    entries = section.get(key)
    if not isinstance(entries, list):
        return dict(section)
    return {**section, key: [_entry(entry, config_dir) for entry in entries]}


def _entry(entry: object, config_dir: Path) -> object:
    """One entry, its photos read from its file.

    Args:
        entry: The raw table.
        config_dir: The folder of `config.toml`.

    Returns:
        The table with its photos; as it was without a file.

    Raises:
        ValueError: The file is missing, outside the folder, or not valid TOML.
    """
    if not isinstance(entry, dict):
        return entry
    file, inline = entry.get(FILE), entry.get(PHOTOS, [])
    if not (isinstance(file, str) and file and isinstance(inline, list)):
        return entry
    path = linked_path(config_dir, file)
    try:
        loaded = tomllib.loads(path.read_text(ENCODING))
    except FileNotFoundError:
        message = _(
            "{file} is missing: restore it, or remove the line file = '{file}' "
            "of config.toml (its photos are then forgotten)"
        )
        raise ValueError(message.format(file=file)) from None
    except (tomllib.TOMLDecodeError, UnicodeDecodeError) as exc:
        message = _("{file} is not valid TOML: {error}")
        raise ValueError(message.format(file=file, error=exc)) from exc
    listed = loaded.get(PHOTOS, [])
    return {**entry, PHOTOS: [*inline, *(listed if isinstance(listed, list) else [])]}
