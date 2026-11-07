"""The trips other grouping values would make, compared with the trips kept (0646)."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.hand_placed import placed_by_hand
from media_hygiene.classify.trip_walk import home_of, trip_town
from media_hygiene.classify.trips import TripFacts, walked_trips
from media_hygiene.classify.whereabouts import point_of

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.event_cut import DatedFiles
    from media_hygiene.classify.models import Event, MediaInput
    from media_hygiene.classify.trip_walk import Group
    from media_hygiene.config.classify_settings import ClassifySettings
    from media_hygiene.geo.distance import Point
    from media_hygiene.geo.gazetteer import Gazetteer

LISTED: Final = 12  # changes listed by kind: the page shows a few, counts them all


@dataclass(frozen=True, slots=True)
class Tried:
    """The two sets of values compared."""

    now: ClassifySettings
    asked: ClassifySettings


def listed(
    changes: Mapping[str, list[dict[str, object]]],
) -> dict[str, dict[str, object]]:
    """Each kind of change: its count and the first `LISTED`.

    Args:
        changes: The changes, by kind.

    Returns:
        What the page reads.
    """
    return {
        kind: {"count": len(found), "listed": found[:LISTED]}
        for kind, found in changes.items()
    }


def _trip_line(
    trip: Sequence[Group], home: Point, towns: Gazetteer
) -> dict[str, object]:
    """One trip of the page: its days, its count, its town."""
    town = trip_town(trip, home, towns)
    return {
        "first": trip[0].start.isoformat(),
        "last": trip[-1].end.isoformat(),
        "files": sum(len(group.paths) for group in trip),
        "town": town.name if town else "",
    }


def _paths(trip: Sequence[Group]) -> frozenset[Path]:
    """The files of a trip."""
    return frozenset(path for group in trip for path in group.paths)


def compared_trips(
    files: Sequence[MediaInput],
    known: tuple[DatedFiles, tuple[Sequence[Event], Sequence[Event]]],
    config: tuple[Tried, Gazetteer | None],
) -> dict[str, object]:
    """The trips with the values kept, and with the values asked.

    Args:
        files: The files.
        known: Their dates, and the events of the values kept and asked.
        config: The two sets of values, and the towns (None: no rule names them).

    Returns:
        `known` False when `classify` would find no trip: no `trip` rule or no home.
        Else `before` and `after` (how many trips), and those that are `new`, `gone`
        (no photo in common) or `changed` (the same photos in part).
    """
    (dated, (before, after)), (tried, towns) = known, config
    home = home_of(tried.now)
    if towns is None or home is None:
        return {"known": False}
    points = {file.path: point for file in files if (point := point_of(file))}
    hand = placed_by_hand(files, tried.now)
    points |= {path: place.point for path, place in hand.items()}
    old = walked_trips(TripFacts(points, before, dated.datings), tried.now, home.point)
    new = walked_trips(TripFacts(points, after, dated.datings), tried.asked, home.point)
    changes = _changes((old, new), lambda trip: _trip_line(trip, home.point, towns))
    return {
        "known": True,
        "before": len(old),
        "after": len(new),
        **listed(changes),
    }


def _changes(
    trips: tuple[list[list[Group]], list[list[Group]]],
    line: Callable[[Sequence[Group]], dict[str, object]],
) -> dict[str, list[dict[str, object]]]:
    """The trips that appear, change or go.

    Args:
        trips: The trips of the values kept and of the values asked.
        line: What the page shows of a trip.

    Returns:
        The lines by kind: `new` and `gone` share no photo with the other values' trips.
    """
    old, new = trips
    old_paths, new_paths = [_paths(one) for one in old], [_paths(one) for one in new]
    kept, asked = set(old_paths), set(new_paths)
    every_old: frozenset[Path] = frozenset().union(*old_paths)
    every_new: frozenset[Path] = frozenset().union(*new_paths)
    changes: dict[str, list[dict[str, object]]] = {"new": [], "gone": [], "changed": []}
    for trip, paths in zip(new, new_paths, strict=True):
        if paths not in kept:
            changes["changed" if paths & every_old else "new"].append(line(trip))
    for trip, paths in zip(old, old_paths, strict=True):
        if paths not in asked and not paths & every_new:
            changes["gone"].append(line(trip))
    return changes
