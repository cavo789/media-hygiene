"""Edit `config.toml` from the map, keeping the user's comments (0231, 0234, 0237).

`tomlkit` edits the document in place; the new text is parsed again before it replaces
the file, atomically: a crash leaves the old file or the new one, never half of it.
Every caller reads its answer back from the disk.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import String, Table

if TYPE_CHECKING:
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

ENCODING: Final = "utf-8"
DECIMALS: Final = 6  # about 10 cm


def loaded(config_file: Path) -> dict[str, dict[str, list[object]]]:
    """The file as plain values.

    Args:
        config_file: `config.toml`.

    Returns:
        Its tables; empty when missing.
    """
    if not config_file.is_file():
        return {}
    return tomllib.loads(config_file.read_text(ENCODING))


def document_of(config_file: Path) -> TOMLDocument:
    """The file as an editable document.

    Args:
        config_file: `config.toml`; missing: an empty one.

    Returns:
        The document.
    """
    text = config_file.read_text(ENCODING) if config_file.is_file() else ""
    return tomlkit.parse(text)


def table_of(document: TOMLDocument, name: str) -> Table:
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


def host_path(path: str) -> String:
    r"""A host path as TOML: a literal string ('C:\Photos') when it can be one.

    Args:
        path: The path, as the user knows it.

    Returns:
        The string item.
    """
    literal = "'" not in path and "\n" not in path
    return tomlkit.string(path, literal=literal)


def write_document(config_file: Path, document: TOMLDocument) -> None:
    """Replace the file, atomically, with a document the next run can read.

    Args:
        config_file: `config.toml`.
        document: Its new content.
    """
    text = tomlkit.dumps(document)
    tomllib.loads(text)  # never write a file the next run cannot read
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(text, ENCODING)
    temporary.replace(config_file)
