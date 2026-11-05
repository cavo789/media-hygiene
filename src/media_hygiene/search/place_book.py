"""Who is in which of my places (0553): by hand first, else by the GPS circle or area.

Read once from the index and `/config`, again when one changed: the index's data
version, `config.toml`, the `places/` folder (a save replaces a file in it).
"""

from __future__ import annotations

import math
from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.classify.hand_placed import Candidate, hand_placed
from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.config.place_files import FOLDER
from media_hygiene.places.config_file import read_places
from media_hygiene.places.config_photos import read_place_photos

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Mapping

    from media_hygiene.classify.place_match import Zone
    from media_hygiene.geo.distance import Point

_FILES: Final = "SELECT path, size, full_digest FROM files"
_VERSION: Final = "PRAGMA data_version"
_METRES_PER_DEGREE: Final = 111_000.0
_MARGIN: Final = 1.1
_LEAST_COSINE: Final = 0.01  # near a pole, the box is every longitude


@dataclass(frozen=True, slots=True)
class PlaceMembers:
    """The photos of each place, by folded name, the located and those given by hand."""

    names: tuple[str, ...]  # as written in `config.toml`
    by_gps: Mapping[str, frozenset[Path]]
    by_hand: Mapping[str, frozenset[Path]]
    located: frozenset[Path]  # every photo with a position, in a place or not

    def of(self, place: str) -> frozenset[Path]:
        """The photos of a place.

        Args:
            place: Its name, any case.

        Returns:
            Those of its circle or area, and those given it by hand.
        """
        name = place.casefold()
        return self.by_gps.get(name, frozenset()) | self.by_hand.get(name, frozenset())

    def placed(self) -> frozenset[Path]:
        """Every photo with a place: located, or given one by hand.

        Returns:
            Them.
        """
        by_hand = frozenset[Path]().union(*self.by_hand.values())
        return self.located | by_hand


@dataclass(slots=True)
class PlaceBook:
    """Keeps the members until the index or the settings change."""

    connection: sqlite3.Connection
    config_file: Path
    points: Callable[[], Mapping[Path, Point]]
    _kept: tuple[object, PlaceMembers] | None = field(default=None)

    def members(self) -> PlaceMembers:
        """The members now.

        Returns:
            Them, read again when something changed.

        Raises:
            ValueError: A place or an entry of the settings is invalid.
        """
        stamp = self._stamp()
        if self._kept is None or self._kept[0] != stamp:
            self._kept = (stamp, self._read())
        return self._kept[1]

    def _stamp(self) -> object:
        """What changes when a member may.

        Returns:
            The index's version and the settings' times.
        """
        version = self.connection.execute(_VERSION).fetchone()[0]
        return (
            version,
            _mtime(self.config_file),
            _mtime(self.config_file.parent / FOLDER),
        )

    def _read(self) -> PlaceMembers:
        """Read the places, the photos given, the positions.

        Returns:
            The members.
        """
        places = read_places(self.config_file)
        by_hand: defaultdict[str, set[Path]] = defaultdict(set)
        given = read_place_photos(self.config_file)
        if given:
            rows = self.connection.execute(_FILES)
            candidates = (Candidate(Path(p), size, sha) for p, size, sha in rows)
            for path, name in hand_placed(candidates, given).items():
                by_hand[name.casefold()].add(path)
        hand = {path for paths in by_hand.values() for path in paths}
        zones = zones_of(places)
        by_gps: defaultdict[str, set[Path]] = defaultdict(set)
        points = self.points()
        for path, point in near_a_zone(points, zones):
            if path not in hand and (found := place_at(point, zones)) is not None:
                by_gps[found.name.casefold()].add(path)
        return PlaceMembers(
            tuple(place.name for place in places),
            {name: frozenset(paths) for name, paths in by_gps.items()},
            {name: frozenset(paths) for name, paths in by_hand.items()},
            frozenset(points),
        )


def near_a_zone(
    points: Mapping[Path, Point], zones: tuple[Zone, ...]
) -> list[tuple[Path, Point]]:
    """The positions inside the box of some place: most of the others never test.

    Measured (50,000 positions, 20 places): 6.9 s testing each one, 0.01 s so.

    Args:
        points: The positions.
        zones: My places, prepared.

    Returns:
        Those worth the exact test.
    """
    if not points or not zones:
        return []
    items = list(points.items())
    latitudes = np.fromiter((p.latitude for _, p in items), float, len(items))
    longitudes = np.fromiter((p.longitude for _, p in items), float, len(items))
    near = np.zeros(len(items), dtype=bool)
    for zone in zones:
        south, west, north, east = _box(zone)
        near |= (
            (latitudes >= south)
            & (latitudes <= north)
            & (longitudes >= west)
            & (longitudes <= east)
        )
    return [items[int(rank)] for rank in np.flatnonzero(near)]


def _box(zone: Zone) -> tuple[float, float, float, float]:
    """A box holding a place, a little too wide.

    Args:
        zone: The place.

    Returns:
        South, west, north, east, in degrees.
    """
    if zone.area is not None:
        bounds = zone.area.bounds
        return bounds.south, bounds.west, bounds.north, bounds.east
    place = zone.place
    lat_span = place.radius_m / _METRES_PER_DEGREE * _MARGIN
    near_pole = max(math.cos(math.radians(place.latitude)), _LEAST_COSINE)
    lon_span = lat_span / near_pole
    return (
        place.latitude - lat_span,
        place.longitude - lon_span,
        place.latitude + lat_span,
        place.longitude + lon_span,
    )


def _mtime(path: Path) -> int:
    """When a file or folder changed.

    Args:
        path: It.

    Returns:
        Its time in nanoseconds; 0 when missing.
    """
    try:
        return path.stat().st_mtime_ns
    except OSError:
        return 0
