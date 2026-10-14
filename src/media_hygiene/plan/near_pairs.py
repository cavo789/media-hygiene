"""The pairs of pictures whose hashes are close, found with numpy (TODO 0152).

Multi-index hashing: two 64-bit hashes at most 2 bits apart share at least one of
their four 16-bit quarters, so only pictures sharing a quarter are compared. The pairs
grow with the square of the collection (≈ 5.5 million at 300,000 synthetic photos):
compared one by one in Python they took most of a warm audit's near-duplicate step.
Here each quarter is sorted, the pictures sharing it are paired by offset, and both
distances and the colours are checked in bulk. Same pairs as `likeness.distance` and
`likeness.same_colours` would keep.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.plan.likeness import COLOUR_FLOOR, COLOUR_SHARE, HASH_BITS

if TYPE_CHECKING:
    from collections.abc import Sequence

    from numpy.typing import NDArray

    from media_hygiene.scan.models import VisualFacts

_QUARTER_BITS: Final = 16
_QUARTER_MASK: Final = (1 << _QUARTER_BITS) - 1


def close_pairs(
    looks: Sequence[VisualFacts], distance: int
) -> tuple[NDArray[np.intp], NDArray[np.intp]]:
    """Positions of the pictures whose pHash and dHash are both within `distance`.

    Args:
        looks: What each picture looks like, by position.
        distance: The largest Hamming distance kept, on each hash.

    Returns:
        The first and second position of each pair (a pair may appear twice).
    """
    phash = np.fromiter((look.phash for look in looks), np.uint64, len(looks))
    dhash = np.fromiter((look.dhash for look in looks), np.uint64, len(looks))
    colour = np.fromiter(
        (np.nan if look.colour is None else look.colour for look in looks),
        np.float64,
        len(looks),
    )
    firsts: list[NDArray[np.intp]] = []
    seconds: list[NDArray[np.intp]] = []
    for quarter in range(HASH_BITS // _QUARTER_BITS):
        keys = (phash >> np.uint64(quarter * _QUARTER_BITS)) & np.uint64(_QUARTER_MASK)
        first, second = _sharing(keys)
        keep = (
            (np.bitwise_count(phash[first] ^ phash[second]) <= distance)
            & (np.bitwise_count(dhash[first] ^ dhash[second]) <= distance)
            & _same_colours(colour[first], colour[second])
        )
        firsts.append(first[keep])
        seconds.append(second[keep])
    return np.concatenate(firsts), np.concatenate(seconds)


def _sharing(keys: NDArray[np.uint64]) -> tuple[NDArray[np.intp], NDArray[np.intp]]:
    """Every pair of positions holding the same key.

    Args:
        keys: One key per picture.

    Returns:
        The first and second position of each pair, the first smaller.
    """
    order = np.argsort(keys, kind="stable")
    ranked = keys[order]
    starts = np.flatnonzero(np.r_[True, ranked[1:] != ranked[:-1]])
    ends = np.r_[starts[1:], len(ranked)]
    run_end = np.repeat(ends, ends - starts)  # where the run of each position ends
    positions = np.arange(len(ranked))
    firsts: list[NDArray[np.intp]] = []
    seconds: list[NDArray[np.intp]] = []
    offset = 1
    active = positions[run_end - positions > offset]
    while active.size:
        left, right = order[active], order[active + offset]
        firsts.append(np.minimum(left, right))
        seconds.append(np.maximum(left, right))
        offset += 1
        active = active[run_end[active] - active > offset]
    if not firsts:
        empty = np.empty(0, dtype=np.intp)
        return empty, empty
    return np.concatenate(firsts), np.concatenate(seconds)


def _same_colours(
    first: NDArray[np.float64], second: NDArray[np.float64]
) -> NDArray[np.bool_]:
    """`likeness.same_colours`, pair by pair: unknown (NaN) agrees with anything.

    Args:
        first: The colourfulness of one picture of each pair.
        second: That of the other.

    Returns:
        False only when one is clearly colourful and the other has less than half.
    """
    low, high = np.minimum(first, second), np.maximum(first, second)
    unknown = np.isnan(first) | np.isnan(second)
    with np.errstate(invalid="ignore"):
        return unknown | (high < COLOUR_FLOOR) | (low > COLOUR_SHARE * high)
