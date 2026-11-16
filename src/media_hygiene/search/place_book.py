"""Who is in which of my places (0553): by hand first, else by the GPS circle or area.

Read once from the index and `/config`, again when one changed: the index's data
version, `config.toml`, the `places/` folder (a save replaces a file in it).
"""

from __future__ import annotations

from collections import defaultdict
from dataclasses import dataclass, field
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.config.place_files import FOLDER
from media_hygiene.places.config_file import read_places
from media_hygiene.places.config_photos import read_place_photos
from media_hygiene.review.slow_log import Laps
from media_hygiene.search.place_boxes import near_a_zone
from media_hygiene.search.placed_where import placed_where

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Callable, Mapping

    from media_hygiene.geo.distance import Point

type Stamp = tuple[int, int, int]  # index data version, two times

_FILES: Final = "SELECT path, size, full_digest FROM files"
_VERSION: Final = "PRAGMA data_version"


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
    _kept: tuple[Stamp, PlaceMembers] | None = field(default=None)

    def members(self) -> PlaceMembers:
        """The members now.

        Returns:
            Them, read again when something changed.

        Raises:
            ValueError: A place or an entry of the settings is invalid.
        """
        stamp = self._stamp()
        if self._kept is None or self._kept[0] != stamp:
            why = "first" if self._kept is None else _changed(self._kept[0], stamp)
            self._kept = (stamp, self._read(Laps(f"places, read again ({why})")))
        return self._kept[1]

    def _stamp(self) -> Stamp:
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

    def _read(self, laps: Laps) -> PlaceMembers:
        """Read the places, the photos given, the positions.

        Args:
            laps: Where the time goes, said when slow.

        Returns:
            The members.
        """
        places = read_places(self.config_file)
        by_hand: defaultdict[str, set[Path]] = defaultdict(set)
        given = read_place_photos(self.config_file)
        laps.lap("settings")
        if given:
            rows = self.connection.execute(_FILES)
            for path, name in placed_where(rows, given).items():
                by_hand[name.casefold()].add(path)
        laps.lap(f"{len(given)} given by hand")
        hand = {path for paths in by_hand.values() for path in paths}
        zones = zones_of(places)
        by_gps: defaultdict[str, set[Path]] = defaultdict(set)
        points = self.points()
        laps.lap(f"{len(points)} positions")
        for path, point in near_a_zone(points, zones):
            if path not in hand and (found := place_at(point, zones)) is not None:
                by_gps[found.name.casefold()].add(path)
        laps.lap(f"{len(places)} places")
        laps.said()
        return PlaceMembers(
            tuple(place.name for place in places),
            {name: frozenset(paths) for name, paths in by_gps.items()},
            {name: frozenset(paths) for name, paths in by_hand.items()},
            frozenset(points),
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


def _changed(before: Stamp, now: Stamp) -> str:
    """Which part of the stamp changed.

    Args:
        before: The stamp kept.
        now: The stamp now.

    Returns:
        `index`, `config.toml`, `places/`: those that changed.
    """
    parts = ("index", "config.toml", "places/")
    changed = zip(parts, before, now, strict=True)
    return ", ".join(part for part, old, new in changed if old != new)
