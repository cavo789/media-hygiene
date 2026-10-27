"""Write `[[places.folders]]` and `[classify] folder_town_ignore` into `config.toml`.

From the map of `places` (0231): the position given a whole folder, or a folder name
that is no town, and back (0235). `toml_edit` keeps the user's comments and replaces
the file atomically; every answer is read back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Array

from media_hygiene.config.places_settings import FolderPosition
from media_hygiene.geo.folding import town_key
from media_hygiene.places.toml_edit import (
    DECIMALS,
    document_of,
    host_path,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

_PLACES: Final = "places"
_FOLDERS: Final = "folders"
_CLASSIFY: Final = "classify"
_IGNORE: Final = "folder_town_ignore"


def read_folders(config_file: Path) -> tuple[FolderPosition, ...]:
    """The folder positions written in the file.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        Them, in their order.

    Raises:
        ValueError: The file or a position is invalid.
    """
    rows = loaded(config_file).get(_PLACES, {}).get(_FOLDERS, [])
    return tuple(FolderPosition.model_validate(row) for row in rows)


def read_ignored(config_file: Path) -> tuple[str, ...]:
    """The folder names that are never towns.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        `[classify] folder_town_ignore`.
    """
    names = loaded(config_file).get(_CLASSIFY, {}).get(_IGNORE, [])
    return tuple(str(name) for name in names)


def save_folder(config_file: Path, position: FolderPosition | str) -> None:
    """Write a folder's position, replacing the one it had; a bare folder forgets it.

    Args:
        config_file: `config.toml`, created when missing.
        position: The position; a host path alone takes the folder's out.
    """
    save_folders(config_file, [position])


def save_folders(config_file: Path, positions: Sequence[FolderPosition | str]) -> None:
    """Write folders' positions in one write; a bare folder forgets its own (0383).

    Args:
        config_file: `config.toml`, created when missing.
        positions: The positions; a host path alone takes the folder's out.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    document = document_of(config_file)
    places = table_of(document, _PLACES)
    rows = places.get(_FOLDERS)
    if not isinstance(rows, AoT):
        rows = tomlkit.aot()
        places.append(_FOLDERS, rows)
    for position in positions:
        folder = position if isinstance(position, str) else position.folder
        for rank in reversed(range(len(rows.body))):
            if str(rows.body[rank].get("folder", "")).casefold() == folder.casefold():
                del rows[rank]
        if not isinstance(position, str):
            table = tomlkit.table()
            table["folder"] = host_path(position.folder)  # 'C:\Photos', as users write
            table["latitude"] = round(position.latitude, DECIMALS)
            table["longitude"] = round(position.longitude, DECIMALS)
            table.add(tomlkit.nl())  # a blank line before what follows
            rows.append(table)
    if not rows.body:
        del places[_FOLDERS]
    write_document(config_file, document)


def ignore_name(config_file: Path, name: str) -> None:
    """Add a folder name to `folder_town_ignore`, once whatever its spelling.

    Args:
        config_file: `config.toml`, created when missing.
        name: The folder's name.

    Raises:
        ValueError: The file is not TOML, or the name is empty.
        OSError: The file cannot be written.
    """
    if not town_key(name):
        raise ValueError(name)
    document = document_of(config_file)
    section = table_of(document, _CLASSIFY)
    names = section.get(_IGNORE)
    if not isinstance(names, Array):
        names = tomlkit.array()
        section[_IGNORE] = names
    if town_key(name) not in {town_key(str(known)) for known in names}:
        names.append(name)
    write_document(config_file, document)


def restore_name(config_file: Path, name: str) -> None:
    """Take a folder name out of `folder_town_ignore`, whatever its spelling.

    Args:
        config_file: `config.toml`.
        name: The name, as the list holds it.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    document = document_of(config_file)
    section = table_of(document, _CLASSIFY)
    names = section.get(_IGNORE)
    if not isinstance(names, Array):
        return
    for rank in reversed(range(len(names))):
        if town_key(str(names[rank])) == town_key(name):
            del names[rank]
    write_document(config_file, document)
