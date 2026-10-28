"""The events of a show, told (0448): each run of photos of one folder gets a chapter.

The place of an event: the user's place (`[[classify.places]]`, a circle or an area)
most of its located photos lie in; else the town nearest to most of them (the offline
GeoNames snapshot, read only when a photo has GPS); else nothing. Nothing leaves the
machine. A town in another country than home comes with it ("Valkenburg, Netherlands"):
home is the country of the place flagged `home`, else of the first place, else the
country most of the show's located photos lie in.
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
from media_hygiene.i18n import _
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.slideshow.chapters import Chapter, event_name, event_period
from media_hygiene.slideshow.event_map import event_map

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.config.classify_places import PersonalPlace
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
        told.extend(replace(slide, chapter=chapter) for slide in slides)
    return tuple(told)


class Places:
    """Names the place of a group of positions: the user's place, else a town."""

    __slots__ = ("_home", "_towns", "_zones")

    def __init__(
        self,
        runtime: Runtime,
        towns: Gazetteer | None,
        everywhere: Sequence[Point] = (),
    ) -> None:
        """Prepare the user's places.

        Args:
            runtime: Settings (`[[classify.places]]`, `[classify] town_names`).
            towns: The GeoNames towns; None when no photo has GPS.
            everywhere: The positions of the whole show (for the home country).
        """
        settings = runtime.settings.classify
        self._zones = zones_of(settings.places)
        self._towns = None if towns is None else towns.renamed(settings.town_names)
        self._home = self._home_country(settings.places, everywhere)

    @property
    def towns(self) -> Gazetteer | None:
        """The towns, named the user's way.

        Returns:
            Them; None when no photo has GPS.
        """
        return self._towns

    def _home_country(
        self, places: Sequence[PersonalPlace], points: Sequence[Point]
    ) -> str:
        """The country the user lives in, as far as the places and photos tell.

        Args:
            places: The user's places.
            points: The positions of the whole show.

        Returns:
            Its name in the language in use; empty when unknown.
        """
        if self._towns is None:
            return ""
        flagged = next((place for place in places if place.home), None)
        if flagged is None and places:
            flagged = places[0]
        if flagged is not None:
            town = self._towns.nearest(flagged.point)
            return town.country if town else ""
        counts = Counter(
            town.country for p in points if (town := self._towns.nearest(p))
        )
        return counts.most_common(1)[0][0] if counts else ""

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
            (town.name, town.country)
            for point in points
            if (town := self._towns.nearest(point))
        )
        if not towns:
            return ""
        name, country = towns.most_common(1)[0][0]
        if self._home and country != self._home:
            return _("{town}, {country}").format(town=name, country=country)
        return name


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
