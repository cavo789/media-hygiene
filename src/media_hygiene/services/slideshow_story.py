"""The events of a show, told (0448): each run of photos of one folder gets a chapter.

The place of an event: the user's place (`[[classify.places]]`, a circle or an area)
most of its located photos lie in; else the town nearest to most of them (the offline
GeoNames snapshot, read only when a photo has GPS); else nothing. Nothing leaves the
machine.
"""

from __future__ import annotations

from collections import Counter
from dataclasses import replace
from itertools import groupby
from typing import TYPE_CHECKING

from pydantic import ValidationError

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.classify.whereabouts import located_point
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.slideshow.chapters import Chapter, event_name, event_period

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
    towns = Gazetteer.load() if any(points.values()) else None
    places = Places(runtime, towns)
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
        )
        told.extend(replace(slide, chapter=chapter) for slide in slides)
    return tuple(told)


class Places:
    """Names the place of a group of positions: the user's place, else a town."""

    __slots__ = ("_towns", "_zones")

    def __init__(self, runtime: Runtime, towns: Gazetteer | None) -> None:
        """Prepare the user's places.

        Args:
            runtime: Settings (`[[classify.places]]`, `[classify] town_names`).
            towns: The GeoNames towns; None when no photo has GPS.
        """
        settings = runtime.settings.classify
        self._zones = zones_of(settings.places)
        self._towns = None if towns is None else towns.renamed(settings.town_names)

    def named(self, points: Sequence[Point]) -> str:
        """The place most of the positions lie at.

        Args:
            points: The positions of an event's located photos.

        Returns:
            The user's place, else the nearest town; empty without a position.
        """
        own = Counter(
            found.name for point in points if (found := place_at(point, self._zones))
        )
        if own:
            return own.most_common(1)[0][0]
        if self._towns is None:
            return ""
        towns = Counter(
            town.name for point in points if (town := self._towns.nearest(point))
        )
        return towns.most_common(1)[0][0] if towns else ""


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
