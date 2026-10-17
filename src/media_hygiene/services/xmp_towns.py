"""The town of each photo without a GPS position, from its folder: what `xmp` writes.

Opt-in (`[tags] xmp_folder_gps`): the position is the town's centre, approximate. The
folders are told by the same guess as the `folder_town` rule (`town_folders`), whether
or not that rule is in `[[classify.rules]]`. A photo the index, or its Takeout `.json`,
locates is never given one.
"""

from __future__ import annotations

from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.classify.town_folders import town_folders
from media_hygiene.classify.whereabouts import located_point
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

    from media_hygiene.geo.gazetteer import Town
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.tags.xmp_merge import XmpValues


def folder_towns_of(
    runtime: Runtime, connection: sqlite3.Connection
) -> Mapping[Path, Town]:
    """The town each unlocated photo's folder is named after.

    Args:
        runtime: Settings and mount points.
        connection: The open index.

    Returns:
        The town of each photo without a position; empty when `xmp_folder_gps` is
        off.
    """
    settings = runtime.settings
    if not settings.tags.xmp_folder_gps:
        return {}
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    files = [
        with_takeout(
            input_of(file, root_of(file.path, roots, runtime), file.facts),
            takeout_of(connection, file.path),
        )
        for file in indexed_files(connection)
    ]
    points = {
        file.path: point
        for file in files
        if (point := located_point(file.metadata)) is not None
    }
    towns = Gazetteer.load().renamed(settings.classify.town_names)
    found = town_folders(files, points, (settings.classify, towns))
    return {
        path: town
        for (_folder, town), paths in found.folders.items()
        for path in paths
        if path not in points
    }


def with_town(values: XmpValues, town: Town | None) -> XmpValues:
    """Add the position of a photo's folder town, and its town and country.

    Args:
        values: What the tags give the photo.
        town: Its folder's town, or None.

    Returns:
        The values; the location fields from the town only when the tags give none.
    """
    if town is None:
        return values
    places = values.places
    if places == NO_PLACES:
        places = XmpPlaces(city=town.name, country=town.country)
    return replace(values, gps=gps_of(town.point), places=places)
