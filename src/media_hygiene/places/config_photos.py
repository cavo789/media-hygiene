"""`[[classify.place_photos]]`: photos given a place from the map (0237, 0551).

From the drawer of a cluster: its photos given to a place already named, one by one,
their GPS being wrong. A photo belongs to one place at most: given again, it leaves the
other. A place renamed on the map renames its entry; a place deleted takes its photos
with it, so that no entry ever names nothing. The photos live in `places/<name>.toml`
(`photo_files`); every answer is read back from the disk.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from tomlkit.items import AoT, Table

from media_hygiene.config.place_files import KEY, SECTION, linked_entries
from media_hygiene.config.place_photos import PlacePhotos
from media_hygiene.places.photo_files import save_entries
from media_hygiene.places.toml_edit import loaded, table_of

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from pathlib import Path

    from tomlkit.toml_document import TOMLDocument

PLACE: Final = "place"


def read_place_photos(config_file: Path) -> tuple[PlacePhotos, ...]:
    """The photos given a place, in the file's order.

    Args:
        config_file: `config.toml`; missing: none.

    Returns:
        The entries.

    Raises:
        ValueError: The file, a linked file or an entry is invalid.
    """
    section = linked_entries(loaded(config_file).get(SECTION, {}), config_file.parent)
    rows = section.get(KEY, [])
    if not isinstance(rows, list):
        return ()
    return tuple(PlacePhotos.model_validate(row) for row in rows)


def give_photos(config_file: Path, given: PlacePhotos) -> None:
    """Add photos to a place's entry, taking them out of any other.

    Args:
        config_file: `config.toml`, created when missing.
        given: The place and its new photos.

    Raises:
        ValueError: A file is not TOML.
        OSError: A file cannot be written.
    """
    entries = _without(read_place_photos(config_file), {p.id for p in given.photos})
    place = given.place.casefold()
    if not any(entry.place.casefold() == place for entry in entries):
        entries.append(PlacePhotos(place=given.place))
    save_entries(
        config_file,
        tuple(
            entry.model_copy(update={"photos": (*entry.photos, *given.photos)})
            if entry.place.casefold() == place
            else entry
            for entry in entries
        ),
    )


def take_back(config_file: Path, photo_id: str) -> None:
    """Take one photo out of every entry: its GPS decides again.

    Args:
        config_file: `config.toml`.
        photo_id: The photo's id.

    Raises:
        ValueError: A file is not TOML.
        OSError: A file cannot be written.
    """
    save_entries(
        config_file, tuple(_without(read_place_photos(config_file), {photo_id}))
    )


def _without(
    entries: tuple[PlacePhotos, ...], ids: Collection[str]
) -> list[PlacePhotos]:
    """The entries, some photos taken out.

    Args:
        entries: The entries.
        ids: The photos' ids.

    Returns:
        Them, in order (an entry left empty is dropped at the save).
    """
    return [
        entry.model_copy(
            update={"photos": tuple(p for p in entry.photos if p.id not in ids)}
        )
        for entry in entries
    ]


def follow_places(document: TOMLDocument, renamed: Mapping[str, str | None]) -> None:
    """Rename the entries of places renamed, drop those of places deleted.

    Args:
        document: `config.toml`, being edited by the places' save.
        renamed: Each old name (any case) and its new one; None: deleted.
    """
    follow = {old.casefold(): new for old, new in renamed.items()}
    section = document.get(SECTION)
    rows = section.get(KEY) if isinstance(section, Table) else None
    if not isinstance(rows, AoT) or not follow:
        return
    for rank in reversed(range(len(rows.body))):
        name = str(rows.body[rank].get(PLACE, "")).casefold()
        if name in follow and (new := follow[name]) is not None:
            rows.body[rank][PLACE] = new
        elif name in follow:
            del rows[rank]
    if not rows.body:
        del table_of(document, SECTION)[KEY]
