"""What only a backup holds, minus what the user already dealt with (0245).

A file only in a backup (0204) is proposed for the library only when its content was
never dealt with: not set aside by a choice before (0216: a burst shot, a near copy,
a file chosen, an unwanted photo; quarantined or purged since), not deleted in the
Explorer (0224, confirmed or still waiting for `review --gone`). Each kept apart is
counted, so a deletion by mistake can still be recovered by hand.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.near import is_featureless, is_near

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.scan.models import MediaFile, VisualFacts

_QUARTER: Final = 0xFFFF


@dataclass(frozen=True, slots=True)
class DealtWith:
    """Paths (container) of a backup's own files whose content was dealt with before.

    `set_aside`: set aside by a choice (0216) or confirmed deleted (0224);
    `deleted`: deleted in the Explorer, the answer still waiting for `review --gone`.
    """

    set_aside: frozenset[Path] = frozenset()
    deleted: frozenset[Path] = frozenset()

    def holds(self, path: Path) -> bool:
        """Tell whether a file's content was dealt with.

        Args:
            path: A file of the backup.

        Returns:
            True when it is not to propose.
        """
        return path in self.set_aside or path in self.deleted


def proposed(only: Iterable[MediaFile], dealt: DealtWith) -> tuple[MediaFile, ...]:
    """The files only in a backup that were never dealt with.

    Args:
        only: The backup's files without an identical copy in the library.
        dealt: What the journals and the index remember.

    Returns:
        Those to propose, in their order.
    """
    return tuple(file for file in only if not dealt.holds(file.path))


def kept_apart(
    only: Iterable[MediaFile], paths: frozenset[Path]
) -> tuple[MediaFile, ...]:
    """The files of `only` among some paths (set aside, deleted).

    Args:
        only: The backup's files without an identical copy in the library.
        paths: The paths of one reason.

    Returns:
        Those files, in their order.
    """
    return tuple(file for file in only if file.path in paths)


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
