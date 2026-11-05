"""0508: a random show walking through time, chapter by chapter."""

from __future__ import annotations

import itertools
from datetime import UTC, datetime, timedelta
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.classify.events import EventRules
from media_hygiene.services import slideshow_random
from media_hygiene.services.slideshow_random import Journey, journey, spread

_RULES: Final = EventRules.of(6, 18, 5)
_START: Final = datetime(2000, 6, 1, 10, 0, 0, tzinfo=UTC)


def _collection(years: int, events: int, photos: int) -> list[tuple[Path, datetime]]:
    """`events` outings a year (a month apart), `photos` shots each, a minute apart."""
    dated: list[tuple[Path, datetime]] = []
    for year in range(years):
        for event in range(events):
            day = _START.replace(year=_START.year + year) + timedelta(days=30 * event)
            dated.extend(
                (
                    Path(f"/data/c/{year}/{event}/{shot:03}.jpg"),
                    day + timedelta(minutes=shot),
                )
                for shot in range(photos)
            )
    return dated


def _when(dated: list[tuple[Path, datetime]]) -> dict[Path, datetime]:
    return dict(dated)


@pytest.mark.parametrize("seed", range(5))
def test_a_chapter_is_in_date_order_and_the_walk_stays_near(seed: int) -> None:
    """Inside a year, oldest first; between chapters, mostly 1 to 3 years away."""
    dated = _collection(20, 5, 3)
    when = _when(dated)
    shown = journey(dated, Journey(10_000, _RULES, seed=seed))
    years = [when[path].year for path in shown]
    chapters = [
        year
        for index, year in enumerate(years)
        if index == 0 or year != years[index - 1]
    ]
    for index in range(1, len(shown)):
        if years[index] == years[index - 1]:
            assert when[shown[index]] > when[shown[index - 1]]
    steps = [abs(after - before) for before, after in itertools.pairwise(chapters)]
    near = sum(step <= slideshow_random.NEIGHBOUR_YEARS for step in steps)
    assert near >= len(steps) * 0.6


def test_every_photo_once_when_fewer_than_asked() -> None:
    """A small collection: each photo once, no loop."""
    dated = _collection(3, 2, 4)
    shown = journey(dated, Journey(10_000, _RULES, seed=1))
    assert sorted(shown) == sorted(path for path, _when in dated)


def test_the_length_and_the_years_are_kept() -> None:
    """At most the slides asked; only the years asked."""
    dated = _collection(10, 5, 20)
    when = _when(dated)
    shown = journey(dated, Journey(50, _RULES, (2003, 2005), seed=2))
    assert len(shown) == 50
    assert {when[path].year for path in shown} <= {2003, 2004, 2005}
    assert len(set(shown)) == len(shown)


def test_an_event_gives_a_few_photos_spread_over_it() -> None:
    """Ten photos of a hundred: the first, the last and between."""
    paths = [Path(f"/p/{index:03}.jpg") for index in range(100)]
    kept = spread(paths)
    assert len(kept) == slideshow_random.PHOTOS_PER_EVENT
    assert kept[0] == paths[0]
    assert kept[-1] == paths[-1]


def test_a_single_event_and_an_empty_collection() -> None:
    """One outing: its photos; nothing: nothing."""
    dated = _collection(1, 1, 3)
    assert len(journey(dated, Journey(100, _RULES))) == 3
    assert journey([], Journey(100, _RULES)) == []


def test_the_same_seed_gives_the_same_show() -> None:
    """Reproducible: a new tap is a new seed."""
    dated = _collection(10, 5, 5)
    first = journey(dated, Journey(100, _RULES, seed=7))
    assert first == journey(dated, Journey(100, _RULES, seed=7))


def test_one_long_trip_fills_the_length_asked() -> None:
    """A single event of 500 photos, 100 slides asked: 100 of them, not 10."""
    dated = _collection(1, 1, 500)
    shown = journey(dated, Journey(100, _RULES, seed=4))
    assert len(set(shown)) == 100
