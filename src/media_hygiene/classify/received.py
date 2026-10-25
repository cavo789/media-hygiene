"""Pictures received by a messaging app: memories, dated the day received (0402).

WhatsApp strips the EXIF date: `IMG-20260512-WA0003.jpg` gives the day it was
**received**, not the moment it was taken. Such a file never shapes an event (its day,
at midnight, would cut or stretch one), its date is trusted no more than a guess
(`[classify] unsure`), and it joins the event whose time is nearest, within
`merge_gap_hours` of the day it names: a guess in that event's folder, to confirm.
Without one, it is a guess of its month.
"""

from __future__ import annotations

from dataclasses import replace
from datetime import datetime, time, timedelta
from typing import TYPE_CHECKING

from media_hygiene.classify.dating_models import DateSource
from media_hygiene.classify.rules.matchers import is_received

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.classify.dating_models import Dating
    from media_hygiene.classify.models import Event, MediaInput
    from media_hygiene.config.classify_settings import ClassifySettings

_DAY = timedelta(days=1)


def received_guesses(
    files: Sequence[MediaInput],
    datings: Mapping[Path, Dating],
    settings: ClassifySettings,
) -> tuple[dict[Path, Dating], frozenset[Path]]:
    """Trust the date of the received pictures no more than a guess.

    Args:
        files: Every file.
        datings: Their dates.
        settings: `[classify] unsure`.

    Returns:
        The dates, those of received pictures dated by their name capped; and these
        pictures.
    """
    received = frozenset(
        file.path
        for file in files
        if is_received(file) and datings[file.path].source is DateSource.NAME
    )
    capped = {
        path: replace(dating, confidence=min(dating.confidence, settings.unsure))
        if path in received
        else dating
        for path, dating in datings.items()
    }
    return capped, received


def join_received(
    received: frozenset[Path],
    datings: Mapping[Path, Dating],
    context: tuple[Sequence[Event], float],
) -> tuple[Event, ...]:
    """The events, each with the received pictures it is the nearest of, within the gap.

    Args:
        received: The received pictures dated by their name.
        datings: Their dates (the day the name gives).
        context: The events, and `merge_gap_hours`.

    Returns:
        The events, the pictures joined at the end of their files.
    """
    events, gap_hours = context
    gap = timedelta(hours=gap_hours)
    joined: dict[str, list[Path]] = {}
    for path in sorted(received):
        when = datings[path].when
        day = datetime.combine(when.date(), time())  # the name gives a day, no hour
        near = [(_distance(day, event), event.start, event) for event in events]
        close = [item for item in near if item[0] <= gap]
        if close:
            event = min(close, key=lambda item: (item[0], item[1]))[2]
            joined.setdefault(event.event_id, []).append(path)
    return tuple(
        replace(event, paths=(*event.paths, *joined[event.event_id]))
        if event.event_id in joined
        else event
        for event in events
    )


def _distance(day: datetime, event: Event) -> timedelta:
    """How far an event lies from a whole day.

    Args:
        day: Midnight of the day a picture names.
        event: An event.

    Returns:
        Zero when they overlap, else the time between them.
    """
    end_of_day = day + _DAY
    if event.end < day:
        return day - event.end
    if event.start > end_of_day:
        return event.start - end_of_day
    return timedelta(0)
