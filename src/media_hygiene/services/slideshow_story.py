"""The events of a show, told (0448): each run of photos of one folder gets a chapter.

The place of an event: the user's place (`[[classify.places]]`, a circle or an area)
most of its located photos lie in; else the town nearest to most of them (the offline
GeoNames snapshot, read only when a photo has GPS); else nothing. Nothing leaves the
machine. A town in another country than home comes with it ("Valkenburg, Netherlands"):
home is the country of the place flagged `home`, else of the first place, else the
country most of the show's located photos lie in. Each located photo also gets its own
place (0472, `Places.spot`): the user's place, else the landmark it was taken at, else
its town; empty when it is the event's place already.
"""

from __future__ import annotations

from dataclasses import replace
from itertools import groupby
from typing import TYPE_CHECKING

from pydantic import ValidationError

from media_hygiene.classify.whereabouts import located_point
from media_hygiene.geo.towns_once import shared_towns
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.services.slideshow_places import Places
from media_hygiene.slideshow.chapters import Chapter, event_name, event_period
from media_hygiene.slideshow.event_map import event_map

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.geo.distance import Point
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.slideshow.slides import Slide

_METADATA = "SELECT metadata FROM files WHERE rowid = ?"


def told_slides(
    runtime: Runtime,
    connection: sqlite3.Connection,
    shown: Sequence[tuple[Slide, Path]],
) -> tuple[Slide, ...]:
    """The slides, each with its event's chapter.

    Args:
        runtime: Settings and mount points.
        connection: The open index.
        shown: Each slide, in the show's order, with its file.

    Returns:
        The slides, in the same order.
    """
    points = {slide.key: _point(connection, slide.key) for slide, _path in shown}
    towns = shared_towns() if any(points.values()) else None
    places = Places(runtime, towns, [point for point in points.values() if point])
    told: list[Slide] = []
    runs = groupby(shown, key=lambda pair: pair[1].parent)
    for number, (folder, run) in enumerate(runs, start=1):
        slides = [slide for slide, _path in run]
        located = [point for slide in slides if (point := points[slide.key])]
        chapter = Chapter(
            number,
            event_name(folder, runtime.locations.data_dir),
            event_period(slide.day for slide in slides),
            places.named(located),
            event_map(located, places.towns),
        )
        told.extend(
            replace(
                slide, chapter=chapter, place=places.spot(points[slide.key], chapter)
            )
            for slide in slides
        )
    return tuple(told)


def _point(connection: sqlite3.Connection, key: int) -> Point | None:
    """The position of a file, as the index knows it.

    Args:
        connection: The open index.
        key: The file's key.

    Returns:
        Its position; None without GPS.
    """
    row = connection.execute(_METADATA, (key,)).fetchone()
    if row is None or not isinstance(row[0], str):
        return None
    try:
        return located_point(MediaMetadata.model_validate_json(row[0]))
    except ValidationError:
        return None
