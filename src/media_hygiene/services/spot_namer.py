"""Work out the row of one position (0545), offline."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.geo.distance import Point, distance_km
from media_hygiene.geo.reverse import rounded
from media_hygiene.index.spot_rows import SpotSource
from media_hygiene.services.place_names import spot_key

if TYPE_CHECKING:
    from collections.abc import Mapping

    from media_hygiene.geo.gazetteer import Gazetteer
    from media_hygiene.geo.landmarks import Landmarks
    from media_hygiene.index.spot_rows import Known
    from media_hygiene.services.runtime import Runtime

_SEPARATOR: Final = " ; "


class SpotNamer:
    """Writes the row of one position."""

    __slots__ = ("_landmarks", "_online", "_renames", "_stamp", "_town_km", "_towns")

    def __init__(
        self,
        runtime: Runtime,
        known: tuple[Gazetteer, Landmarks, Mapping[str, str]],
        stamp: str,
    ) -> None:
        """Keep what names a position.

        Args:
            runtime: Settings.
            known: The towns, the landmarks, the OpenStreetMap names kept.
            stamp: The stamp of this run.
        """
        self._towns, self._landmarks, self._online = known
        self._stamp = stamp
        self._town_km = runtime.settings.tags.town_km
        self._renames = runtime.settings.classify.town_names

    def row(self, known: Known) -> tuple[object, ...]:
        """The columns of a file's row.

        Args:
            known: The file and its former row.

        Returns:
            The columns of `spots`.
        """
        point = Point(known.latitude, known.longitude)
        landmark, source = self._landmark(known, point)
        town = self._towns.nearest(point)
        if town is None or distance_km(point, town.point) > self._town_km:
            names: tuple[str, ...] = ("", "", "", "")
            words: tuple[str, ...] = (landmark,)
        else:
            names = (town.name, town.region, town.district, town.code)
            words = (
                landmark,
                town.name,
                self._renames.get(town.name, ""),
                town.region,
                town.district,
                *self._towns.countries_of(town.code).values(),
            )
        spoken = _SEPARATOR.join(dict.fromkeys(word for word in words if word))
        place = (known.path, known.latitude, known.longitude, self._stamp)
        return (*place, landmark, source, *names, spoken)

    def _landmark(self, known: Known, point: Point) -> tuple[str, str]:
        """The landmark of a position, and who named it.

        Args:
            known: The file and its former row.
            point: Its position.

        Returns:
            The name typed by hand, else OpenStreetMap's, else GeoNames', else none.
        """
        same = known.stored_at == (known.latitude, known.longitude)
        if same and known.source == SpotSource.USER:
            return known.landmark or "", SpotSource.USER.value
        online = self._online.get(spot_key(rounded(point)), "")
        if online:
            return online, SpotSource.OSM.value
        found = self._landmarks.at(point)
        return found, (SpotSource.GEONAMES if found else SpotSource.NONE).value
