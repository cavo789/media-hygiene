"""Backup files probably in the library already, as a near copy (0245).

Kept apart from `backup_import`: the near-duplicate test of the audit brings numpy,
which the start of the tool must not load (`tests/unit/test_start_imports.py`).
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.plan.near import is_featureless, is_near

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.scan.models import VisualFacts

_QUARTER: Final = 0xFFFF


def near_present(
    candidates: Mapping[Path, VisualFacts], library: Iterable[VisualFacts]
) -> frozenset[Path]:
    """The candidates whose near copy is in the library: "probably already there".

    A HEIC on the NAS and its JPG in the library, a copy resized: the near-duplicate
    test of the audit (`plan.near.is_near`), the larger one as the reference. Images
    sharing no 16-bit quarter of their gradient hash cannot be near (multi-index
    hashing, as `plan.near_pairs`); featureless images never are.

    Args:
        candidates: The backup's images to import, with their visual facts.
        library: The library's images.

    Returns:
        The candidates to list apart, not to propose.
    """
    by_quarter: dict[tuple[int, int], list[VisualFacts]] = {}
    for visual in library:
        for key in _quarters(visual.dhash):
            by_quarter.setdefault(key, []).append(visual)
    near: set[Path] = set()
    for path, visual in candidates.items():
        if is_featureless(visual):
            continue
        seen = (
            other
            for key in _quarters(visual.dhash)
            for other in by_quarter.get(key, ())
        )
        if any(_alike(visual, other) for other in seen):
            near.add(path)
    return frozenset(near)


def _alike(first: VisualFacts, second: VisualFacts) -> bool:
    """Tell whether one image is a near copy of the other, the larger first.

    Args:
        first: An image.
        second: Another one.

    Returns:
        True when `is_near` agrees.
    """
    if first.width * first.height >= second.width * second.height:
        return is_near(first, second)
    return is_near(second, first)


def _quarters(dhash: int) -> tuple[tuple[int, int], ...]:
    """The four 16-bit quarters of a hash, each with its position.

    Args:
        dhash: A 64-bit hash.

    Returns:
        (position, quarter) four times.
    """
    return tuple((index, (dhash >> (16 * index)) & _QUARTER) for index in range(4))
