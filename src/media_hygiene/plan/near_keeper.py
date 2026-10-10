"""Which version of near duplicates to keep, and why.

The highest resolution first. At the same resolution, the larger file is the less
compressed one, but only a difference of 1 % or more says so: two exports of one clip,
or a copy whose metadata alone changed, differ by a few bytes that say nothing of their
quality. Between those, the usual keep rules choose, as for identical files.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import KeepReason, NearReason

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.scan.models import MediaFile

# Sizes closer than this share say nothing of the quality.
SIZE_TOLERANCE: Final = 0.01


@dataclass(frozen=True, slots=True)
class NearChoice:
    """The version kept, and the criterion that decided."""

    keeper: MediaFile
    reason: NearReason
    rule: KeepReason | None = None


def choose_keeper(
    cluster: Sequence[MediaFile],
    pixels: Callable[[MediaFile], int],
    policy: KeepPolicy,
) -> NearChoice:
    """Choose the version to keep among alike pictures or videos.

    Args:
        cluster: The versions, two or more.
        pixels: The displayed resolution of a version.
        policy: Protected folders and the usual keep rules.

    Returns:
        The version kept and why.
    """
    top = max(pixels(file) for file in cluster)
    sharpest = [file for file in cluster if pixels(file) == top]
    if len(sharpest) == 1:
        return NearChoice(sharpest[0], NearReason.RESOLUTION)
    largest = max(file.size for file in sharpest)
    close = [file for file in sharpest if file.size >= largest * (1 - SIZE_TOLERANCE)]
    if len(close) == 1:
        return NearChoice(close[0], NearReason.SIZE)
    return rules_choice(close, policy)


def rules_choice(candidates: Sequence[MediaFile], policy: KeepPolicy) -> NearChoice:
    """Let the usual keep rules choose between versions worth the same.

    Args:
        candidates: The versions, two or more.
        policy: Protected folders and the usual keep rules.

    Returns:
        The version kept, and the rule that ranked it before the next one.
    """
    keeper, runner_up = sorted(candidates, key=policy.rank)[:2]
    return NearChoice(keeper, NearReason.RULES, policy.reason(keeper, runner_up))
