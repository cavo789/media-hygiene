"""A random show that travels through time, chapter by chapter (0508).

The dated photos are cut into events by `classify`'s gaps (`find_events`); a chapter is
one year: a few of its events, oldest first, a handful of photos each, spread over the
event's duration. The next chapter is a neighbouring year (a random walk), with now and
then a larger jump so that the show does not stay in one era; a year comes back only
once every other one was shown. A pure function of the photos and the seed: a new tap
on the phone is a new seed.
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
EVENTS_PER_CHAPTER: Final = (4, 6)  # fewest, most
NEIGHBOUR_YEARS: Final = 3  # the walk's step: 1 to 3 years away
JUMP_CHANCE: Final = 0.15  # now and then, any year left


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
        At most `asked.slides` photos, each once: chapter by chapter, each oldest first.
    """
    rules = EventRules(asked.rules.session_gap, asked.rules.merge_gap, 1)
    by_year: dict[int, list[Event]] = {}
    for event in find_events(dated, rules, {}):
        year = event.start.year
        if asked.years is None or asked.years[0] <= year <= asked.years[1]:
            by_year.setdefault(year, []).append(event)
    chance = random.Random(asked.seed)  # noqa: S311 - a show, not a secret
    # Few events for the length asked (a long trip): more photos of each.
    events = sum(len(each) for each in by_year.values())
    per = max(PHOTOS_PER_EVENT, -(-asked.slides // max(events, 1)))
    shown: list[Path] = []
    seen: set[int] = set()
    chapter = chance.choice(sorted(by_year)) if by_year else None
    while chapter is not None and len(shown) < asked.slides:
        shown.extend(_chapter(by_year, (chapter, per), chance))
        seen.add(chapter)
        chapter = _next_year(by_year, (chapter, seen), chance)
    return shown[: asked.slides]


def _chapter(
    by_year: dict[int, list[Event]], slot: tuple[int, int], chance: random.Random
) -> list[Path]:
    """A few events of the year not shown yet, oldest first; they leave the pool.

    Args:
        by_year: The events still to show, by year.
        slot: The chapter's year, and the photos taken of each event.
        chance: The show's random source.

    Returns:
        Their photos.
    """
    year, per = slot
    left = by_year[year]
    count = min(len(left), chance.randint(*EVENTS_PER_CHAPTER))
    taken = sorted(chance.sample(left, count), key=lambda event: event.start)
    for event in taken:
        left.remove(event)
    if not left:
        del by_year[year]
    return [path for event in taken for path in spread(event.paths, per)]


def _next_year(
    by_year: dict[int, list[Event]], walk: tuple[int, set[int]], chance: random.Random
) -> int | None:
    """A neighbouring year not shown in this round; now and then any year left.

    Args:
        by_year: The events still to show, by year.
        walk: The year just shown, and the years shown in this round (emptied when
            every year left was shown).
        chance: The show's random source.

    Returns:
        The next chapter's year; None when every event was shown.
    """
    here, seen = walk
    if not by_year:
        return None
    if seen >= by_year.keys():
        seen.clear()
        seen.add(here)  # a new round, not the same year twice in a row
    fresh = sorted(year for year in by_year if year not in seen) or sorted(by_year)
    if chance.random() < JUMP_CHANCE:
        return chance.choice(fresh)
    near = [year for year in fresh if abs(year - here) <= NEIGHBOUR_YEARS]
    closest = min(abs(year - here) for year in fresh)
    return chance.choice(
        near or [year for year in fresh if abs(year - here) == closest]
    )


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
