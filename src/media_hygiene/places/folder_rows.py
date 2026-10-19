"""The lines of the folders' list of the map page, `config.toml` read again (0231).

A folder is listed when it holds photos without GPS and either its name is a town's
(the guess of the `folder_town` rule, the ignored names read back) or the user gave it
a position (`[[places.folders]]`). A saved folder that no longer exists (renamed in
Explorer, moved by `sort`) is listed too, as not found: never an error.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.classify.town_folders import town_folders
from media_hygiene.constants import MediaKind
from media_hygiene.places.config_folders import read_folders, read_ignored
from media_hygiene.scan.filters import media_kind

if TYPE_CHECKING:
    from collections.abc import Iterable
    from pathlib import Path

    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.config.places_settings import FolderPosition
    from media_hygiene.geo.gazetteer import Gazetteer, Town
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.services.xmp_towns import IndexedInputs


@dataclass(frozen=True, slots=True)
class FolderContext:
    """What the list needs besides the files: the file, the paths, the towns."""

    config_file: Path
    mapper: HostPathMapper
    settings: ClassifySettings  # the threshold, home; the ignored names read back
    towns: Gazetteer
    roots: tuple[Path, ...] = ()  # the mounted folders: the tree's tops (0242)


@dataclass(frozen=True, slots=True)
class FolderRow:  # pylint: disable=too-many-instance-attributes  # one per column
    """One folder of the list."""

    folder: str  # host path
    town: str
    country: str
    latitude: float
    longitude: float
    saved: bool
    found: bool
    photos: tuple[Path, ...]  # those without a position


def folder_rows(inputs: IndexedInputs, context: FolderContext) -> tuple[FolderRow, ...]:
    """List the folders, `config.toml` read again.

    Args:
        inputs: Every file of the index and the positions.
        context: The file, the paths, the towns.

    Returns:
        The rows, the most photos without a position first.
    """
    ignored = read_ignored(context.config_file)
    settings = context.settings.model_copy(update={"folder_town_ignore": ignored})
    found = town_folders(inputs.files, inputs.points, (settings, context.towns))
    rows: dict[str, FolderRow] = {}
    for (folder, town), paths in found.folders.items():
        alone = tuple(path for path in paths if path not in inputs.points)
        if alone:
            host = context.mapper.to_host(folder)
            rows[host.casefold()] = _named(host, town, alone)
    for position in read_folders(context.config_file):
        key = position.folder.casefold()
        rows[key] = _saved(position, rows.get(key), (inputs, context))
    return tuple(sorted(rows.values(), key=lambda row: (-len(row.photos), row.folder)))


def folders_json(rows: Iterable[FolderRow]) -> list[dict[str, object]]:
    """Write the list for the page; a line's rank is the one `GET /api/folder/` names.

    Args:
        rows: The folders.

    Returns:
        Each folder's town, position, saved or not, found or not, its files
        without a position and how many of them are videos.
    """
    return [
        {
            "rank": rank,
            "folder": row.folder,
            "town": row.town,
            "country": row.country,
            "latitude": row.latitude,
            "longitude": row.longitude,
            "saved": row.saved,
            "found": row.found,
            "count": len(row.photos),
            "videos": sum(media_kind(path) is MediaKind.VIDEO for path in row.photos),
        }
        for rank, row in enumerate(rows)
    ]


def _named(host: str, town: Town, photos: tuple[Path, ...]) -> FolderRow:
    """The line of a folder named after a town, not placed yet.

    Args:
        host: Its host path.
        town: Its town.
        photos: Its photos without a position.

    Returns:
        The row, at the town's centre.
    """
    return FolderRow(
        host,
        town.name,
        town.country,
        town.point.latitude,
        town.point.longitude,
        saved=False,
        found=True,
        photos=photos,
    )


def _saved(
    position: FolderPosition,
    named: FolderRow | None,
    where: tuple[IndexedInputs, FolderContext],
) -> FolderRow:
    """The line of a folder the user placed.

    Args:
        position: Its saved position.
        named: Its line as a folder named after a town, or None.
        where: The files, and the paths.

    Returns:
        The row, at the saved position.
    """
    inputs, context = where
    folder = context.mapper.to_container(position.folder)
    photos = (
        named.photos
        if named is not None
        else tuple(
            file.path
            for file in inputs.files
            if file.path not in inputs.points and file.path.is_relative_to(folder)
        )
    )
    return FolderRow(
        position.folder,
        named.town if named else "",
        named.country if named else "",
        position.latitude,
        position.longitude,
        saved=True,
        found=folder.is_dir(),
        photos=photos,
    )
