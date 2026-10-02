"""Write `[[classify.places]]` into `config.toml`, keeping the user's comments.

`tomlkit` edits the document in place: a place already written keeps its comments and
its position; a new one follows the others, or ends the file when it is the first. The
file is replaced atomically: a crash leaves the old one or the new one, never half.
"""

from __future__ import annotations

import tomllib
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Table

from media_hygiene.config.classify_places import PersonalPlace, check_places

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

SECTION: Final = "classify"
KEY: Final = "places"
_ENCODING: Final = "utf-8"
_DECIMALS: Final = 6  # about 10 cm


@dataclass(frozen=True, slots=True)
class PlaceEdit:
    """One place as the page sends it: `key` is its rank in the file, None if new."""

    key: int | None
    place: PersonalPlace


def read_places(config_file: Path) -> tuple[PersonalPlace, ...]:
    """The places written in the file, in their order.

    Args:
        config_file: `config.toml`; missing: no place.

    Returns:
        The places.

    Raises:
        ValueError: The file or a place is invalid.
    """
    if not config_file.is_file():
        return ()
    loaded = tomllib.loads(config_file.read_text(_ENCODING))
    rows = loaded.get(SECTION, {}).get(KEY, [])
    return tuple(PersonalPlace.model_validate(row) for row in rows)


def save_places(config_file: Path, edits: Sequence[PlaceEdit]) -> None:
    """Write the places, replacing those of the file.

    Args:
        config_file: `config.toml`, created when missing.
        edits: Every place, kept ones with their key.

    Raises:
        ValueError: Two places share a name, or two are home; the file is not TOML.
        OSError: The file cannot be written.
    """
    check_places([edit.place for edit in edits])
    text = config_file.read_text(_ENCODING) if config_file.is_file() else ""
    document = tomlkit.parse(text)
    written = _written(document)
    kept = {edit.key: edit.place for edit in edits if edit.key is not None}
    new = [edit.place for edit in edits if edit.key is None or edit.key not in written]
    for key in sorted(written, reverse=True):
        if key in kept:
            _fill(written[key], kept[key])
        else:
            del document[SECTION][KEY][key]
    result = _append(document, new)
    tomllib.loads(result)  # never write a file the next run cannot read
    temporary = config_file.with_name(f".{config_file.name}.tmp")
    temporary.write_text(result, _ENCODING)
    temporary.replace(config_file)


def _written(document: TOMLDocument) -> dict[int, Table]:
    """The place tables of the document, by rank.

    Args:
        document: The parsed file.

    Returns:
        Them; none when the section holds no array of tables.
    """
    section = document.get(SECTION)
    places = section.get(KEY) if isinstance(section, Table) else None
    if not isinstance(places, AoT):
        if isinstance(section, Table) and KEY in section:
            del section[KEY]  # an inline array: written again as tables
        return {}
    return dict(enumerate(places.body))


def _append(document: TOMLDocument, new: Sequence[PersonalPlace]) -> str:
    """Add the new places after the others, or at the end of the file.

    Args:
        document: The parsed file, kept places already updated.
        new: The places to add.

    Returns:
        The text to write.
    """
    section = document.get(SECTION)
    places = section.get(KEY) if isinstance(section, Table) else None
    if isinstance(places, AoT):
        for place in new:
            table = _fill(tomlkit.table(), place)
            table.add(tomlkit.nl())  # a blank line before what follows
            places.append(table)
        if not places.body:
            del document[SECTION][KEY]
        return tomlkit.dumps(document)
    text = tomlkit.dumps(document).rstrip()
    blocks = [
        f"[[{SECTION}.{KEY}]]\n{tomlkit.dumps(_fill(tomlkit.table(), p)).rstrip()}"
        for p in new
    ]
    return "\n\n".join(part for part in (text, *blocks) if part).rstrip() + "\n"


def _fill(table: Table, place: PersonalPlace) -> Table:
    """Write one place into its table, keeping the table's comments.

    Args:
        table: The table, empty or as written.
        place: The place.

    Returns:
        The table.
    """
    table["name"] = place.name
    table["latitude"] = round(place.latitude, _DECIMALS)
    table["longitude"] = round(place.longitude, _DECIMALS)
    radius = place.radius_m
    table["radius_m"] = int(radius) if radius.is_integer() else radius
    if place.home:
        table["home"] = True
    elif "home" in table:
        del table["home"]
    return table
