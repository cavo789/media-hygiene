"""How the search page shows a rule tried (0396): which files, where each one goes.

Shown: the files the rule takes, those of its days, and those of the events sharing a
day with it (an event the rule leaves whole when most of its files fall outside its
days: its photos are shown too, so that the user sees why, and may widen the period).
"""

from __future__ import annotations

from datetime import date
from typing import TYPE_CHECKING, Final

from media_hygiene.search.rule_models import SEPARATOR

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.rules.calendar import OneOff
    from media_hygiene.search.models import Hit
    from media_hygiene.search.rule_models import Tried

WINDOWS: Final = "\\"


def reaches(tried: Iterable[Tried], days: tuple[date, date]) -> bool:
    """Tell whether an event reaches the first or last day read: it may go on.

    Args:
        tried: Where each file read would go, and its event.
        days: The first and last day read.

    Returns:
        True when an event starts on the first day or ends on the last one.
    """
    edges = {day.isoformat() for day in days}
    return any(
        where.event is not None and (where.event[0] in edges or where.event[1] in edges)
        for where in tried
    )


def shown_in(hit: Hit, tried: Mapping[Path, Tried], window: OneOff) -> bool:
    """Tell whether a file is shown: taken, of the rule's days, or of their events.

    Args:
        hit: The file.
        tried: Where each file would go.
        window: The rule's days.

    Returns:
        True when it is.
    """
    where = tried.get(hit.photo.path)
    if where is not None and (where.taken or _touches(where.event, window)):
        return True
    return hit.date is not None and window.contains(date.fromisoformat(hit.date))


def _touches(event: tuple[str, str, int] | None, window: OneOff) -> bool:
    """Tell whether an event shares a day with the rule's: its photos are shown.

    Args:
        event: Its first and last day, its files; None: no event.
        window: The rule's days.

    Returns:
        True when it does.
    """
    if event is None:
        return False
    first, last = date.fromisoformat(event[0]), date.fromisoformat(event[1])
    return first <= window.end and window.start <= last


def where_of(tried: Tried | None) -> dict[str, object]:
    """Where one file would go, for its card.

    Args:
        tried: What the trial said of it; None: not classified (not a media file).

    Returns:
        `to` (the folder, as Windows writes it; empty: it stays), `by` (the rule that
        decides), `taken`.
    """
    if tried is None:
        return {"to": "", "by": "", "taken": False}
    folder = (tried.folder or "").replace(SEPARATOR, WINDOWS)
    return {"to": folder, "by": tried.rule, "taken": tried.taken}


def wider(
    hits: Sequence[Hit], tried: Mapping[Path, Tried], window: OneOff
) -> list[dict[str, object]]:
    """The events the rule leaves because most of their files fall outside its days.

    A date rule takes an event when at least half of its files fall on its days: an
    evening shot on two days, typed as one, is left whole. The page then offers to
    widen the period to the event's days.

    Args:
        hits: The files shown.
        tried: Where each file would go, and its event.
        window: The rule's days.

    Returns:
        Each such event's first and last day, its files, and how many of them are on
        the rule's days.
    """
    events: dict[tuple[str, str, int], int] = {}
    for hit in hits:
        where = tried.get(hit.photo.path)
        if where is None or where.taken or where.event is None:
            continue
        first, last, _files = where.event
        inside = window.contains(date.fromisoformat(first)) and window.contains(
            date.fromisoformat(last)
        )
        on_days = hit.date is not None and window.contains(date.fromisoformat(hit.date))
        if not inside:
            events[where.event] = events.get(where.event, 0) + on_days
    return [
        {"first": first, "last": last, "files": files, "here": here}
        for (first, last, files), here in events.items()
    ]
