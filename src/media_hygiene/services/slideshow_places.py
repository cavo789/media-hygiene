"""Where the photos of a show were taken: an event's place, each photo's (0448, 0472).

The user's place (`[[classify.places]]`) first; for a photo, the name OpenStreetMap
gave its spot once the user said Yes after an import (0474, `services.place_names`),
else the landmark of the offline GeoNames snapshot it was taken at (`geo.landmarks`);
else the nearest town. Nothing is sent from here.
"""

from __future__ import annotations

from collections import Counter
from typing import TYPE_CHECKING

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.geo.landmarks import shared_landmarks
from media_hygiene.geo.reverse import rounded
from media_hygiene.i18n import _
from media_hygiene.services.place_names import read_names, spot_key
from media_hygiene.slideshow.chapters import told_place

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.geo.distance import Point
    from media_hygiene.geo.gazetteer import Gazetteer
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.slideshow.chapters import Chapter


class Places:
    """Names the place of a group of positions: the user's place, else a town."""

    __slots__ = ("_home", "_landmarks", "_online", "_towns", "_zones")

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
        self._landmarks = None if towns is None else shared_landmarks()
        self._online = read_names(runtime.locations.cache_dir)  # said Yes to (0474)

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
        return self._abroad(name, country)

    def spot(self, point: Point | None, chapter: Chapter) -> str:
        """The place of one photo (0472), told on the TV when it adds something.

        Args:
            point: The photo's position; None without GPS.
            chapter: Its event, whose name and place the banner already says.

        Returns:
            The user's place it lies in, else the name OpenStreetMap gave it, else
            the landmark it was taken at, else its town; empty without GPS, or when
            the event's name or place says it.
        """
        if point is None:
            return ""
        own = place_at(point, self._zones)
        spot = own.name if own else self._online.get(spot_key(rounded(point)), "")
        if not spot and self._landmarks is not None:
            spot = self._landmarks.at(point)
        if not spot and self._towns is not None:
            town = self._towns.nearest(point)
            spot = self._abroad(town.name, town.country) if town else ""
        return told_place(f"{chapter.name} {chapter.place}", spot)

    def _abroad(self, name: str, country: str) -> str:
        """A town's name, with its country when it is not home's.

        Args:
            name: The town.
            country: Its country.

        Returns:
            E.g. `Valkenburg, Netherlands`, or `Liège` at home.
        """
        if self._home and country != self._home:
            return _("{town}, {country}").format(town=name, country=country)
        return name
