"""Where each photo without a GPS position was taken, by its folder: what `xmp` writes.

Opt-in (`[tags] xmp_folder_gps`). The nearest folder above the photo decides: a
position the user gave it on the map of `places` (`[[places.folders]]`, 0231), else the
centre of the town it is named after, approximate. The towns are told by the same guess
as the `folder_town` rule (`town_folders`), whether or not that rule is in
`[[classify.rules]]`. A photo the index, or its Takeout `.json`, locates gets nothing.
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from media_hygiene.classify.town_folders import town_folders
from media_hygiene.classify.whereabouts import located_point
from media_hygiene.geo.distance import Point
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.index.listing import indexed_files
from media_hygiene.index.takeout_rows import takeout_of
from media_hygiene.services.classify_inputs import input_of, root_of, with_takeout
from media_hygiene.tags.xmp_gps import gps_of
from media_hygiene.tags.xmp_places import NO_PLACES, XmpPlaces

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.classify.models import MediaInput
    from media_hygiene.geo.gazetteer import Town
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.tags.xmp_merge import XmpValues


@dataclass(frozen=True, slots=True)
class FolderSpot:
    """Where a photo without GPS was taken, by its folder."""

    point: Point
    name: str  # the town, else the folder's name: what the dry run counts
    town: Town | None = None  # its folder's town, for the location fields


@dataclass(frozen=True, slots=True)
class FolderSpots:
    """The spot of each photo without GPS, and the saved folders not found."""

    spots: Mapping[Path, FolderSpot] = field(default_factory=dict["Path", FolderSpot])
    missing: tuple[str, ...] = ()  # host paths: renamed, moved, or not mounted


@dataclass(frozen=True, slots=True)
class IndexedInputs:
    """Every file of the index as `classify` sees it, and where the located ones lie."""

    files: tuple[MediaInput, ...]
    points: Mapping[Path, Point]


def indexed_inputs(runtime: Runtime, connection: sqlite3.Connection) -> IndexedInputs:
    """Read every file of the index, its Takeout position included.

    Args:
        runtime: Mount points.
        connection: The open index.

    Returns:
        The files and the positions.
    """
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    files = tuple(
        with_takeout(
            input_of(file, root_of(file.path, roots, runtime), file.facts),
            takeout_of(connection, file.path),
        )
        for file in indexed_files(connection)
    )
    points = {
        file.path: point
        for file in files
        if (point := located_point(file.metadata)) is not None
    }
    return IndexedInputs(files, points)


def saved_folders(runtime: Runtime) -> tuple[dict[Path, Point], tuple[str, ...]]:
    """The positions of `[[places.folders]]`, in container paths.

    Args:
        runtime: Settings and the path mapper.

    Returns:
        The folders found, and the host paths of those that are not.
    """
    found: dict[Path, Point] = {}
    missing: list[str] = []
    for saved in runtime.settings.places.folders:
        folder = runtime.mapper.to_container(saved.folder)
        if folder.is_dir():
            found[folder] = Point(saved.latitude, saved.longitude)
        else:
            missing.append(saved.folder)
    return found, tuple(missing)


def folder_spots(runtime: Runtime, connection: sqlite3.Connection) -> FolderSpots:
    """The spot of each unlocated photo, from its folder.

    Args:
        runtime: Settings and mount points.
        connection: The open index.

    Returns:
        The spots; none when `xmp_folder_gps` is off.
    """
    settings = runtime.settings
    if not settings.tags.xmp_folder_gps:
        return FolderSpots()
    inputs = indexed_inputs(runtime, connection)
    towns = Gazetteer.load().renamed(settings.classify.town_names)
    found = town_folders(inputs.files, inputs.points, (settings.classify, towns))
    named = {
        path: (folder, town)
        for (folder, town), paths in found.folders.items()
        for path in paths
    }
    saved, missing = saved_folders(runtime)
    spots: dict[Path, FolderSpot] = {}
    for file in inputs.files:
        if file.path in inputs.points:
            continue
        spot = _spot(file.path, named.get(file.path), saved)
        if spot is not None:
            spots[file.path] = spot
    return FolderSpots(spots, missing)


def _spot(
    path: Path, named: tuple[Path, Town] | None, saved: Mapping[Path, Point]
) -> FolderSpot | None:
    """The nearest folder above a photo that has a saved position or a town's name.

    Args:
        path: The photo.
        named: Its folder named after a town, and that town; None.
        saved: The positions the user gave folders.

    Returns:
        Its spot, or None.
    """
    folder, town = named if named is not None else (None, None)
    for parent in path.parents:
        here = town if parent == folder else None
        if parent in saved:
            return FolderSpot(saved[parent], here.name if here else parent.name, here)
        if here is not None:
            return FolderSpot(here.point, here.name, here)
    return None


def with_spot(values: XmpValues, spot: FolderSpot | None) -> XmpValues:
    """Add the position a photo's folder gives, and its town and country.

    Args:
        values: What the tags give the photo.
        spot: Its folder's spot, or None.

    Returns:
        The values; the location fields from the town only when the tags give none.
    """
    if spot is None:
        return values
    places = values.places
    if places == NO_PLACES and spot.town is not None:
        places = XmpPlaces(city=spot.town.name, country=spot.town.country)
    return replace(values, gps=gps_of(spot.point), places=places)
