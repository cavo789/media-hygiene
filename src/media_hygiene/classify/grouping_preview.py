"""The events as other grouping values would make them, before they are kept (0643).

The same cut as `events.find_events` (a gap longer than the larger of the session and
merge gaps starts a new group; a group smaller than the minimum is no event), on the
times alone: two groupings compared, the events that merge, split, appear or go
listed. Nothing is written: the page shows it, then saves the values or not.
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import timedelta
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime

LISTED: Final = 12  # changes listed by kind: the page shows a few, counts them all

type Span = tuple[int, int]  # first and last index into the sorted times


@dataclass(frozen=True, slots=True)
class Grouping:
    """The values that cut the photos into events."""

    session_hours: float
    merge_hours: float
    min_size: int


def event_spans(times: Sequence[datetime], grouping: Grouping) -> list[Span]:
    """The events of sorted times, as index ranges.

    Args:
        times: When each photo was taken, oldest first.
        grouping: The gaps and the minimum size.

    Returns:
        The first and last index of each event, oldest first.
    """
    gap = timedelta(hours=max(grouping.session_hours, grouping.merge_hours))
    spans: list[Span] = []
    start = 0
    for index in range(1, len(times) + 1):
        if index == len(times) or times[index] - times[index - 1] > gap:
            if index - start >= grouping.min_size:
                spans.append((start, index - 1))
            start = index
    return spans


def _within(spans: Sequence[Span], span: Span) -> int:
    """How many of `spans` overlap `span`."""
    return sum(1 for one in spans if one[0] <= span[1] and span[0] <= one[1])


def _change(times: Sequence[datetime], span: Span, parts: int) -> dict[str, object]:
    """One event of the page: its days, its count, how many of the others it holds."""
    return {
        "first": times[span[0]].isoformat(),
        "last": times[span[1]].isoformat(),
        "files": span[1] - span[0] + 1,
        "parts": parts,
    }


def compared(
    times: Sequence[datetime], now: Grouping, asked: Grouping
) -> dict[str, object]:
    """The events with the values kept, and with the values asked.

    Args:
        times: When each photo was taken, oldest first.
        now: The values `config.toml` holds.
        asked: The values the page is trying.

    Returns:
        `before` and `after` (`events`, `files` in one), and the changes by kind:
        `merged` (an event asked holding several kept ones), `split` (a kept one cut
        into several), `new` and `gone`; each a count and the first `LISTED`.
    """
    before, after = event_spans(times, now), event_spans(times, asked)
    kept, tried = set(before), set(after)
    changes: dict[str, list[dict[str, object]]] = {
        "merged": [],
        "split": [],
        "new": [],
        "gone": [],
    }
    for span in after:
        if span not in kept and (parts := _within(before, span)) != 1:
            changes["merged" if parts else "new"].append(_change(times, span, parts))
    for span in before:
        if span not in tried and (parts := _within(after, span)) != 1:
            changes["split" if parts else "gone"].append(_change(times, span, parts))
    return {
        "before": _totals(before),
        "after": _totals(after),
        **{
            kind: {"count": len(found), "listed": found[:LISTED]}
            for kind, found in changes.items()
        },
    }


def _totals(spans: Sequence[Span]) -> dict[str, int]:
    """How many events, and how many photos in one."""
    return {
        "events": len(spans),
        "files": sum(last - first + 1 for first, last in spans),
    }
