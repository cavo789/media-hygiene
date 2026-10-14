"""The numpy pair search keeps exactly the pairs the one-by-one tests kept (0152)."""

from __future__ import annotations

import random
from collections import defaultdict
from itertools import combinations
from typing import Final

from media_hygiene.plan.likeness import distance, same_colours
from media_hygiene.plan.near_pairs import close_pairs
from media_hygiene.scan.models import VisualFacts

_DISTANCE: Final = 2
_QUARTERS: Final = 4
_MASK: Final = 0xFFFF


def _flip(value: int, bits: int, rng: random.Random) -> int:
    """Flip some bits of a 64-bit hash."""
    for bit in rng.sample(range(64), bits):
        value ^= 1 << bit
    return value


def _looks(count: int, seed: int) -> list[VisualFacts]:
    """Scenes of shots a few bits apart, near copies, colours known or not."""
    rng = random.Random(seed)  # noqa: S311 - test data, not a secret
    looks: list[VisualFacts] = []
    while len(looks) < count:
        phash, dhash = rng.getrandbits(64), rng.getrandbits(64)
        for _ in range(rng.randint(1, 12)):
            colour = rng.choice((None, 3.0, 20.0, 45.0))
            looks.append(
                VisualFacts(
                    dhash=_flip(dhash, rng.randint(0, 4), rng),
                    phash=_flip(phash, rng.randint(0, 4), rng),
                    width=40,
                    height=30,
                    sharpness=1.0,
                    colour=colour,
                )
            )
    return looks


def _reference(looks: list[VisualFacts]) -> set[tuple[int, int]]:
    """The pairs as `near._clusters` found them before, one by one."""
    buckets: defaultdict[tuple[int, int], list[int]] = defaultdict(list)
    for index, look in enumerate(looks):
        for quarter in range(_QUARTERS):
            buckets[(quarter, (look.phash >> (16 * quarter)) & _MASK)].append(index)
    return {
        (first, second)
        for members in buckets.values()
        for first, second in combinations(members, 2)
        if distance(looks[first].phash, looks[second].phash) <= _DISTANCE
        and distance(looks[first].dhash, looks[second].dhash) <= _DISTANCE
        and same_colours(looks[first].colour, looks[second].colour)
    }


def test_the_same_pairs_as_one_by_one() -> None:
    """Several random sets, colours known or not: identical pairs."""
    for seed in range(5):
        looks = _looks(1500, seed)
        firsts, seconds = close_pairs(looks, _DISTANCE)
        found = set(zip(firsts.tolist(), seconds.tolist(), strict=True))
        assert found == _reference(looks)


def test_nothing_to_pair() -> None:
    """One picture, or pictures sharing no quarter: no pair."""
    one = _looks(1, 0)[:1]
    firsts, _seconds = close_pairs(one, _DISTANCE)
    assert not firsts.size
