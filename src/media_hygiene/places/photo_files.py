"""Save `[[classify.place_photos]]`: one file of photos per place, linked (0551).

Each place's photos are written to `places/<name>.toml` as `{path, id}` lines
(`config.photo_ref`), atomically; then `config.toml` is edited with `tomlkit`, its
comments kept: each entry holds its place and `file`, the photos still inline (before
0551) move out. An entry left without photos goes, and so does its file.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.config.photo_ref_files import (
    LinkedFile,
    LinkPlace,
    free_file,
    save_linked,
)
from media_hygiene.config.place_files import FOLDER, KEY, SECTION
from media_hygiene.i18n import _
from media_hygiene.people.person_files import safe_name

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.config.place_photos import PlacePhotos

SUFFIX: Final = ".toml"
PLACE: Final = "place"


def file_of(entry: PlacePhotos, taken: set[str]) -> str:
    """The file of a place's photos: the one written, else one after its name.

    Args:
        entry: The place's entry.
        taken: The files already given (case folded), completed here.

    Returns:
        The file, relative to the folder of `config.toml`.
    """
    return free_file(entry.file, f"{FOLDER}/{safe_name(entry.place)}", taken)


def save_entries(config_file: Path, entries: tuple[PlacePhotos, ...]) -> None:
    """Write every place's photos to its file, then link them from `config.toml`.

    Args:
        config_file: `config.toml`, created when missing.
        entries: Every entry, in order; those without photos are dropped.

    Raises:
        ValueError: A file leads out of the folder, or does not read back.
        OSError: A file cannot be written.
    """
    kept = [entry for entry in entries if entry.photos]
    taken = {entry.file.casefold() for entry in kept if entry.file}
    header = _("The photos given {place} on the map; config.toml links this file.")
    linked = [
        LinkedFile(e.place, file_of(e, taken), e.photos, header.format(place=e.place))
        for e in kept
    ]
    save_linked(config_file, LinkPlace(SECTION, KEY, PLACE, FOLDER), linked)
