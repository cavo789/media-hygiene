"""Write `[[places.folders]]` and `[classify] folder_town_ignore` into `config.toml`.

From the map of `places` (0231): the position given a whole folder, or a folder name
that is no town. Like the places (`config_file`), `tomlkit` keeps the user's comments,
the file is checked before it replaces the old one, atomically, and every answer is
read back from the disk.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Array, Table

from media_hygiene.config.places_settings import FolderPosition
from media_hygiene.geo.folding import town_key

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

_PLACES: Final = "places"
_FOLDERS: Final = "folders"
_CLASSIFY: Final = "classify"
_IGNORE: Final = "folder_town_ignore"
_ENCODING: Final = "utf-8"
_DECIMALS: Final = 6  # about 10 cm


def read_folders(config_file: Path) -> tuple[FolderPosition, ...]:
    """The folder positions written in the file.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        Them, in their order.

    Raises:
        ValueError: The file or a position is invalid.
    """
    rows = _loaded(config_file).get(_PLACES, {}).get(_FOLDERS, [])
    return tuple(FolderPosition.model_validate(row) for row in rows)


def read_ignored(config_file: Path) -> tuple[str, ...]:
    """The folder names that are never towns.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        `[classify] folder_town_ignore`.
    """
    names = _loaded(config_file).get(_CLASSIFY, {}).get(_IGNORE, [])
    return tuple(str(name) for name in names)


def save_folder(config_file: Path, position: FolderPosition | str) -> None:
    """Write a folder's position, replacing the one it had; a bare folder forgets it.

    Args:
        config_file: `config.toml`, created when missing.
        position: The position; a host path alone takes the folder's out.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    folder = position if isinstance(position, str) else position.folder
    document = _document(config_file)
    places = _table(document, _PLACES)
    rows = places.get(_FOLDERS)
    if not isinstance(rows, AoT):
        rows = tomlkit.aot()
        places.append(_FOLDERS, rows)
    for rank in reversed(range(len(rows.body))):
        if str(rows.body[rank].get("folder", "")).casefold() == folder.casefold():
            del rows[rank]
    if not isinstance(position, str):
        table = tomlkit.table()
        # 'C:\Photos': a literal string, as the user writes paths, when it can be one.
        literal = "'" not in position.folder and "\n" not in position.folder
        table["folder"] = tomlkit.string(position.folder, literal=literal)
        table["latitude"] = round(position.latitude, _DECIMALS)
        table["longitude"] = round(position.longitude, _DECIMALS)
        table.add(tomlkit.nl())  # a blank line before what follows
        rows.append(table)
    if not rows.body:
        del places[_FOLDERS]
    _write(config_file, document)


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
    document = _document(config_file)
    section = _table(document, _CLASSIFY)
    names = section.get(_IGNORE)
    if not isinstance(names, Array):
        names = tomlkit.array()
        section[_IGNORE] = names
    if town_key(name) not in {town_key(str(known)) for known in names}:
        names.append(name)
    _write(config_file, document)


def _loaded(config_file: Path) -> dict[str, dict[str, list[object]]]:
    """The file as plain values.

    Args:
        config_file: `config.toml`.

    Returns:
        Its tables; empty when missing.
    """
    if not config_file.is_file():
        return {}
    return tomllib.loads(config_file.read_text(_ENCODING))


def _document(config_file: Path) -> TOMLDocument:
    """The file as an editable document.

    Args:
        config_file: `config.toml`; missing: an empty one.

    Returns:
        The document.
    """
    text = config_file.read_text(_ENCODING) if config_file.is_file() else ""
    return tomlkit.parse(text)


def _table(document: TOMLDocument, name: str) -> Table:
    """A top-level table of the document, added at its end when missing.

    Args:
        document: The document.
        name: The table's name.

    Returns:
        The table.
    """
    found = document.get(name)
    if isinstance(found, Table):
        return found
    table = tomlkit.table()
    document[name] = table
    return table


def _write(config_file: Path, document: TOMLDocument) -> None:
    """Replace the file, atomically, with a document the next run can read.

    Args:
        config_file: `config.toml`.
        document: Its new content.
    """
    text = tomlkit.dumps(document)
    tomllib.loads(text)  # never write a file the next run cannot read
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(text, _ENCODING)
    temporary.replace(config_file)
