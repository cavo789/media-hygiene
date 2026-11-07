"""The events and trips other grouping values would make, unsaved (0643, 0646).

The real cut (`event_cut`, `trips`), run twice over the files `classify` works on: the
values kept against the values asked; the events that merge, split, appear or go and
the trips that appear, change or go listed. Nothing is written: the page shows it, then
saves the values or not.
"""

from __future__ import annotations

from bisect import bisect_left, bisect_right
from typing import TYPE_CHECKING

from media_hygiene.classify.engine import run_rules
from media_hygiene.classify.event_cut import dated_files, events_of
from media_hygiene.classify.grouping_trips import Tried, compared_trips, listed

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

    from media_hygiene.classify.engine import Scope
    from media_hygiene.classify.models import Event, MediaInput

type _Key = tuple[datetime, datetime, int]


def _key(event: Event) -> _Key:
    """What tells two cuts of the same files apart."""
    return (event.start, event.end, len(event.paths))


def _change(event: Event, parts: int) -> dict[str, object]:
    """One event of the page: its days, its count, how many of the others it holds."""
    return {
        "first": event.start.isoformat(),
        "last": event.end.isoformat(),
        "files": len(event.paths),
        "parts": parts,
    }


def compared_events(
    before: Sequence[Event], after: Sequence[Event]
) -> dict[str, object]:
    """The events with the values kept, and with the values asked.

    Args:
        before: The events of the values kept, oldest first.
        after: The events of the values asked, oldest first.

    Returns:
        `before` and `after` (`events`, `files` in one), and the changes by kind:
        `merged` (an event asked holding several kept ones), `split` (a kept one cut
        into several), `new` and `gone`; each a count and the first few.
    """
    kept, tried = {_key(one) for one in before}, {_key(one) for one in after}
    changes: dict[str, list[dict[str, object]]] = {
        "merged": [],
        "split": [],
        "new": [],
        "gone": [],
    }
    for event in after:
        if _key(event) not in kept and (parts := _overlaps(before, event)) != 1:
            changes["merged" if parts else "new"].append(_change(event, parts))
    for event in before:
        if _key(event) not in tried and (parts := _overlaps(after, event)) != 1:
            changes["split" if parts else "gone"].append(_change(event, parts))
    return {
        "before": _totals(before),
        "after": _totals(after),
        **listed(changes),
    }


def _overlaps(events: Sequence[Event], event: Event) -> int:
    """How many of `events`, disjoint and in order, share time with `event`."""
    last = bisect_right(events, event.end, key=lambda one: one.start)
    return max(0, last - bisect_left(events, event.start, key=lambda one: one.end))


def _totals(events: Sequence[Event]) -> dict[str, int]:
    """How many events, and how many photos in one."""
    return {
        "events": len(events),
        "files": sum(len(event.paths) for event in events),
    }


def previewed(
    files: Sequence[MediaInput], tried: Tried, scope: Scope
) -> dict[str, object]:
    """Compare the events and the trips of two sets of grouping values.

    Args:
        files: The files `classify` works on.
        tried: The values kept and the values asked.
        scope: The generic folders, the people and the towns.

    Returns:
        `compared_events`, with `trips` (`compared_trips`).
    """
    dated = dated_files(files, tried.now, run_rules(tried.now, scope))
    before, after = events_of(dated, tried.now), events_of(dated, tried.asked)
    return {
        **compared_events(before, after),
        "trips": compared_trips(files, (dated, (before, after)), (tried, scope.towns)),
    }
