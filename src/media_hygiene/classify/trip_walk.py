"""The walk that turns events, in date order, into trips."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.geo.distance import distance_km

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime, timedelta
    from pathlib import Path

    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.distance import Point
    from media_hygiene.geo.gazetteer import Gazetteer, Town

TOWN_RADIUS_KM: Final = 10.0  # a larger town this close names the trip


@dataclass(frozen=True, slots=True)
class Group:
    """An event, or a located file that belongs to none."""

    paths: tuple[Path, ...]
    start: datetime
    end: datetime
    centre: Point | None  # None: no file of it has GPS
    located: int = 0


class TripWalk:
    """Groups in date order become trips."""

    def __init__(self, home: Point, limits: tuple[timedelta, float, float]) -> None:
        """Start with no trip.

        Args:
            home: Where home is.
            limits: The merge gap, the minimum distance from home, the largest
                distance between two days of one trip.
        """
        self._home = home
        self._gap, self._min_km, self._max_km = limits
        self._trips: list[list[Group]] = []
        self._current: list[Group] = []
        self._pending: list[Group] = []  # without GPS: join only if the trip goes on

    def add(self, group: Group) -> None:
        """Read the next group.

        Args:
            group: It, later than every group read so far.
        """
        tail = self._pending or self._current
        if tail and group.start - tail[-1].end > self._gap:
            self._close()
        if group.centre is None:
            if self._current:
                self._pending.append(group)
            return
        if distance_km(group.centre, self._home) <= self._min_km:
            self._close()
            return
        previous = self._current[-1].centre if self._current else None
        if previous is not None and distance_km(group.centre, previous) > self._max_km:
            self._close()
        self._current.extend(self._pending)
        self._pending = []
        self._current.append(group)

    def finish(self) -> list[list[Group]]:
        """End the walk.

        Returns:
            The trips, each a list of groups.
        """
        self._close()
        return self._trips

    def _close(self) -> None:
        """End the current trip, if any; groups without GPS after it stay out."""
        if self._current:
            self._trips.append(self._current)
        self._current, self._pending = [], []


def home_of(settings: ClassifySettings) -> PersonalPlace | None:
    """The personal place marked as home.

    Args:
        settings: `[classify]`.

    Returns:
        It; None without one: no trip can be found.
    """
    return next((place for place in settings.places if place.home), None)


def trip_town(trip: Sequence[Group], home: Point, towns: Gazetteer) -> Town | None:
    """The largest town near the largest located event of a trip.

    Args:
        trip: Its groups.
        home: Where home is: the fallback of a trip without a position.
        towns: The GeoNames towns.

    Returns:
        The town; None when none is near.
    """
    largest = max(trip, key=lambda group: group.located)
    return towns.main_town(largest.centre or home, TOWN_RADIUS_KM)
