"""Trips: events far from home, joined over several days by time and distance.

An event whose files lie, in the middle, farther than `trip_min_km` from home is away.
Away events closer in time than `trip_merge_gap_hours` and in space than
`trip_merge_max_km` form one trip: by distance, not by town, so that a tour of
villages stays one trip. An event without GPS between two days of a trip joins it. A
trip is named after the largest town near its largest located event.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import GeoValues
from media_hygiene.classify.models import DateSource
from media_hygiene.classify.trip_walk import Group, TripWalk
from media_hygiene.classify.whereabouts import (
    Spot,
    Whereabouts,
    place_spots,
    point_of,
)
from media_hygiene.geo.distance import centre

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.models import Dating, Event, MediaInput
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.distance import Point
    from media_hygiene.geo.gazetteer import Gazetteer

TOWN_RADIUS_KM: Final = 10.0  # a larger town this close names the trip


@dataclass(frozen=True, slots=True)
class TripFacts:
    """What trips are found from: positions, events and dates."""

    points: Mapping[Path, Point]
    events: Sequence[Event]
    datings: Mapping[Path, Dating]


def find_whereabouts(
    files: Sequence[MediaInput],
    known: tuple[Sequence[Event], Mapping[Path, Dating]],
    config: tuple[ClassifySettings, Gazetteer | None],
) -> Whereabouts:
    """Where each file was taken: at a personal place, on a trip.

    Args:
        files: The files.
        known: The events and the date of each file.
        config: `[classify]`, and the GeoNames towns when a trip rule is on.

    Returns:
        The files at a personal place and those on a trip.
    """
    settings, towns = config
    events, datings = known
    points = {file.path: point for file in files if (point := point_of(file))}
    if not points:
        return Whereabouts()
    return Whereabouts(
        place_spots(points, events, settings.places),
        trip_spots(TripFacts(points, events, datings), settings, towns),
    )


def trip_spots(
    facts: TripFacts, settings: ClassifySettings, towns: Gazetteer | None
) -> dict[Path, Spot]:
    """The files on a trip.

    Args:
        facts: Positions, events and dates.
        settings: `[classify]`: places and the trip thresholds.
        towns: The GeoNames towns; None: no trip rule is on.

    Returns:
        The trip of each file on one.
    """
    home = next((place for place in settings.places if place.home), None)
    if towns is None or home is None:
        return {}
    walk = TripWalk(
        home.point,
        (
            timedelta(hours=settings.trip_merge_gap_hours),
            settings.trip_min_km,
            settings.trip_merge_max_km,
        ),
    )
    for group in sorted(_groups(facts), key=lambda group: group.start):
        walk.add(group)
    spots: dict[Path, Spot] = {}
    for trip in walk.finish():
        largest = max(trip, key=lambda group: group.located)
        town = towns.main_town(largest.centre or home.point, TOWN_RADIUS_KM)
        values = (
            GeoValues(country=town.country, region=town.region, city=town.name)
            if town
            else GeoValues()
        )
        for group in trip:
            for path in group.paths:
                spots[path] = Spot(values, inherited=path not in facts.points)
    return spots


def _groups(facts: TripFacts) -> list[Group]:
    """The events, and each located file with a trusted date outside of them.

    Args:
        facts: Positions, events and dates.

    Returns:
        The groups, unordered.
    """
    groups = [_group(event.paths, facts) for event in facts.events]
    in_events = {path for event in facts.events for path in event.paths}
    groups.extend(
        _group((path,), facts)
        for path in facts.points
        if path not in in_events
        and (dating := facts.datings.get(path)) is not None
        and dating.source is not DateSource.MTIME
    )
    return groups


def _group(paths: tuple[Path, ...], facts: TripFacts) -> Group:
    """Describe some files taken together.

    Args:
        paths: The files, in date order.
        facts: Positions and dates.

    Returns:
        The group: its span and the middle of its located files.
    """
    located = [facts.points[path] for path in paths if path in facts.points]
    return Group(
        paths,
        facts.datings[paths[0]].when,
        facts.datings[paths[-1]].when,
        centre(located) if located else None,
        len(located),
    )
