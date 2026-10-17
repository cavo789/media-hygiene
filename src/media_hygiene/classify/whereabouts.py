"""Where each file was taken, from the GPS: at a personal place, or on a trip.

Facts for the `place` and `trip` rules, computed once per run. A file without GPS
inherits the place of its event when at least half of the event's located files lie
there, and the trip its event belongs to (`place-neighbour`, `trip-neighbour`).
"""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.layout import GeoValues
from media_hygiene.classify.place_match import place_at, zones_of
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.geo.distance import Point
from media_hygiene.geo.gazetteer import Gazetteer

_TOWN_RULES: Final = frozenset({RuleMatch.TRIP, RuleMatch.FOLDER_TOWN})

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.former import FormerHint
    from media_hygiene.classify.layout import Values
    from media_hygiene.classify.models import Event, MediaInput
    from media_hygiene.config.classify_places import PersonalPlace
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.scan.metadata import MediaMetadata


@dataclass(frozen=True, slots=True)
class Spot:
    """Where a file was taken; `inherited`: from its event, it has no GPS itself."""

    values: GeoValues
    inherited: bool = False
    hint: FormerHint | None = None  # a folder of removed copies named the town (0208)


@dataclass(frozen=True, slots=True)
class Whereabouts:
    """The files at a personal place, on a trip, in a folder named after a town."""

    places: Mapping[Path, Spot] = field(default_factory=dict)
    trips: Mapping[Path, Spot] = field(default_factory=dict)
    folder_towns: Mapping[Path, Spot] = field(default_factory=dict)

    def values(self, path: Path) -> GeoValues:
        """What the layouts can say of where one file was taken.

        Args:
            path: The file.

        Returns:
            Its place, and the country, region and town of its trip (else of the
            town its folder is named after).
        """
        trip = self.trips.get(path) or self.folder_towns.get(path)
        place = self.places.get(path)
        found = trip.values if trip else GeoValues()
        return replace(found, place=place.values.place) if place else found


def with_place(values: Values, geo: GeoValues) -> Values:
    """Layout values, completed with where the file was taken.

    Args:
        values: Its date, category and event.
        geo: Its place and trip.

    Returns:
        The values, with `{place}`, `{country}`, `{region}` and `{city}`.
    """
    return replace(values, geo=geo)


def point_of(file: MediaInput) -> Point | None:
    """The position a file records.

    Args:
        file: The file.

    Returns:
        Its position; None without GPS, or at 0, 0 (a receiver without a fix).
    """
    return located_point(file.metadata)


def located_point(metadata: MediaMetadata | None) -> Point | None:
    """The position some metadata record.

    Args:
        metadata: What the index knows of a file.

    Returns:
        Its position; None without GPS, or at 0, 0 (a receiver without a fix).
    """
    if metadata is None or metadata.latitude is None or metadata.longitude is None:
        return None
    if metadata.latitude == metadata.longitude == 0:
        return None
    return Point(metadata.latitude, metadata.longitude)


def load_towns(settings: ClassifySettings) -> Gazetteer | None:
    """The GeoNames towns, the user's names applied, when a run names towns.

    Args:
        settings: `[classify]`.

    Returns:
        The towns; None when no `trip` or `folder_town` rule is on.
    """
    if not needs_towns(settings):
        return None
    return Gazetteer.load().renamed(settings.town_names)


def needs_towns(settings: ClassifySettings) -> bool:
    """Tell whether a run names towns: a `trip` or `folder_town` rule is on.

    Args:
        settings: `[classify]`.

    Returns:
        True when the GeoNames towns must be read.
    """
    return any(rule.match in _TOWN_RULES and rule.score != 0 for rule in settings.rules)


def place_spots(
    points: Mapping[Path, Point],
    events: Sequence[Event],
    places: Sequence[PersonalPlace],
) -> dict[Path, Spot]:
    """The files at a personal place: by their GPS, or by their event.

    Args:
        points: The position of each located file.
        events: The events.
        places: The user's places.

    Returns:
        The place of each file at one.
    """
    if not places:
        return {}
    zones = zones_of(places)
    own = {
        path: found.name
        for path, point in points.items()
        if (found := place_at(point, zones)) is not None
    }
    spots = {path: Spot(GeoValues(place=name)) for path, name in own.items()}
    for event in events:
        located = [path for path in event.paths if path in points]
        names = Counter(own[path] for path in located if path in own)
        if not names:
            continue
        name, count = names.most_common(1)[0]
        if 2 * count < len(located):
            continue
        for path in event.paths:
            if path not in points:
                spots[path] = Spot(GeoValues(place=name), inherited=True)
    return spots
