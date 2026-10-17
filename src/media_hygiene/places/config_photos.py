"""Write `[[classify.place_photos]]` into `config.toml`: photos given a place (0237).

From the drawer of a cluster: its photos given to a place already named, one by one,
their GPS being wrong. A photo belongs to one place at most: given again, it leaves the
other. A place renamed on the map renames its entry; a place deleted takes its photos
with it, so that no entry ever names nothing. Comments kept, every answer read back.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import tomlkit
from tomlkit.items import AoT, Array, InlineTable, Table

from media_hygiene.config.place_photos import PlacePhotos
from media_hygiene.places.toml_edit import (
    document_of,
    host_path,
    loaded,
    table_of,
    write_document,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

    from media_hygiene.config.place_photos import HandPhoto

SECTION: Final = "classify"
KEY: Final = "place_photos"


def read_place_photos(config_file: Path) -> tuple[PlacePhotos, ...]:
    """The photos given a place, in the file's order.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        The entries.

    Raises:
        ValueError: The file or an entry is invalid.
    """
    rows = loaded(config_file).get(SECTION, {}).get(KEY, [])
    return tuple(PlacePhotos.model_validate(row) for row in rows)


def give_photos(config_file: Path, given: PlacePhotos) -> None:
    """Add photos to a place's entry, taking them out of any other.

    Args:
        config_file: `config.toml`, created when missing.
        given: The place and its new photos.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    document = document_of(config_file)
    rows = _existing(document)
    if rows is None:
        rows = tomlkit.aot()
        table_of(document, SECTION).append(KEY, rows)
    _drop(rows, {photo.sha256 for photo in given.photos})
    place = given.place.casefold()
    entry = next((row for row in rows.body if _name(row) == place), None)
    if entry is None:
        entry = tomlkit.table()
        if not rows.body:
            entry.trivia.indent = "\n"  # a blank line after the table before it
        entry["place"] = given.place
        entry["photos"] = tomlkit.array().multiline(multiline=True)
        entry.add(tomlkit.nl())  # a blank line before what follows
        rows.append(entry)
    photos = entry["photos"]
    if isinstance(photos, Array):
        for photo in given.photos:
            photos.append(_photo(photo))
    write_document(config_file, document)


def take_back(config_file: Path, sha256: str) -> None:
    """Take one photo out of every entry: its GPS decides again.

    Args:
        config_file: `config.toml`.
        sha256: The photo's digest.

    Raises:
        ValueError: The file is not TOML.
        OSError: The file cannot be written.
    """
    document = document_of(config_file)
    rows = _existing(document)
    if rows is not None:
        _drop(rows, {sha256})
        _close(document, rows)
        write_document(config_file, document)


def follow_places(document: TOMLDocument, renamed: Mapping[str, str | None]) -> None:
    """Rename the entries of places renamed, drop those of places deleted.

    Args:
        document: `config.toml`, being edited by the places' save.
        renamed: Each old name (any case) and its new one; None: deleted.
    """
    follow = {old.casefold(): new for old, new in renamed.items()}
    rows = _existing(document)
    if rows is None or not follow:
        return
    for rank in reversed(range(len(rows.body))):
        name = _name(rows.body[rank])
        if name in follow and (new := follow[name]) is not None:
            rows.body[rank]["place"] = new
        elif name in follow:
            del rows[rank]
    _close(document, rows)


def _existing(document: TOMLDocument) -> AoT | None:
    """The entries of the document, if it holds any.

    Args:
        document: The document.

    Returns:
        Them, or None.
    """
    section = document.get(SECTION)
    rows = section.get(KEY) if isinstance(section, Table) else None
    return rows if isinstance(rows, AoT) else None


def _name(row: Table) -> str:
    """An entry's place, case folded, to compare.

    Args:
        row: The entry.

    Returns:
        Its name.
    """
    return str(row.get("place", "")).casefold()


def _drop(rows: AoT, shas: set[str]) -> None:
    """Take some photos out of every entry; an entry left without any goes.

    Args:
        rows: The entries.
        shas: The photos' digests.
    """
    for rank in reversed(range(len(rows.body))):
        photos = rows.body[rank].get("photos")
        if not isinstance(photos, Array):
            continue
        for index in reversed(range(len(photos))):
            item = photos[index]
            if isinstance(item, dict) and item.get("sha256") in shas:
                del photos[index]
        if not photos:
            del rows[rank]


def _close(document: TOMLDocument, rows: AoT) -> None:
    """Remove the list of entries when it is empty.

    Args:
        document: The document.
        rows: Its entries.
    """
    if not rows.body:
        del table_of(document, SECTION)[KEY]


def _photo(photo: HandPhoto) -> InlineTable:
    """One photo as an inline table: `{ sha256 = "…", size = 1234, path = '…' }`.

    Args:
        photo: The photo.

    Returns:
        The table.
    """
    table = tomlkit.inline_table()
    table["sha256"] = photo.sha256
    table["size"] = photo.size
    table["path"] = host_path(photo.path)
    return table
