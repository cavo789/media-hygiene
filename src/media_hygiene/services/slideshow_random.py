"""A random show that travels through time, from the oldest to the newest (0508).

The dated photos are cut into events by `classify`'s gaps (`find_events`); the show
draws events at random until its length is filled, a handful of photos each, spread
over the event's duration, then shows them oldest first: the years only move forward.
An event of fewer than `FEWEST_PHOTOS` photos (one shot of a day) is drawn only when
the larger ones do not fill the show. A pure function of the photos and the seed: a
new tap on the phone is a new seed.
"""

from __future__ import annotations

import random
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.events import EventRules, find_events

if TYPE_CHECKING:
    from collections.abc import Sequence
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.classify.models import Event

PHOTOS_PER_EVENT: Final = 10
FEWEST_PHOTOS: Final = 5  # an event shown has at least these, when it has them


@dataclass(frozen=True, slots=True)
class Journey:
    """What the show asks: how many slides, which years, which seed."""

    slides: int
    rules: EventRules
    years: tuple[int, int] | None = None  # first and last year, both kept
    seed: int = 0


def journey(dated: Sequence[tuple[Path, datetime]], asked: Journey) -> list[Path]:
    """The photos of the show, in its order.

    Args:
        dated: Each photo and its date (photos only, undated ones left out).
        asked: The number of slides, the years, the seed.

    Returns:
        At most `asked.slides` photos, each once, oldest first.
    """
    rules = EventRules(asked.rules.session_gap, asked.rules.merge_gap, 1)
    events = [
        event
        for event in find_events(dated, rules, {})
        if asked.years is None or asked.years[0] <= event.start.year <= asked.years[1]
    ]
    chance = random.Random(asked.seed)  # noqa: S311 - a show, not a secret
    # Few events for the length asked (a long trip): more photos of each.
    per = max(PHOTOS_PER_EVENT, -(-asked.slides // max(len(events), 1)))
    drawn: list[Event] = []
    count = 0
    for event in _draw(events, chance):
        if count >= asked.slides:
            break
        drawn.append(event)
        count += min(len(event.paths), per)
    drawn.sort(key=lambda event: event.start)
    shown = [path for event in drawn for path in spread(event.paths, per)]
    return shown[: asked.slides]


def _draw(events: list[Event], chance: random.Random) -> list[Event]:
    """Every event in a random order, the small ones last.

    Args:
        events: The events of the years asked.
        chance: The show's random source.

    Returns:
        The events of `FEWEST_PHOTOS` photos or more shuffled, then the others.
    """
    large = [event for event in events if len(event.paths) >= FEWEST_PHOTOS]
    small = [event for event in events if len(event.paths) < FEWEST_PHOTOS]
    chance.shuffle(large)
    chance.shuffle(small)
    return large + small


def spread(paths: Sequence[Path], per: int = PHOTOS_PER_EVENT) -> list[Path]:
    """At most `per` photos, spread over the event, not its first ones.

    Args:
        paths: The event's photos, in date order.
        per: How many (at least 2).

    Returns:
        The photos kept, in date order.
    """
    if len(paths) <= per:
        return list(paths)
    last = len(paths) - 1
    return [paths[round(index * last / (per - 1))] for index in range(per)]
