"""What the burst review proposes to set aside, and why: facts compared within a series.

Every shot of a series shows the same scene, so comparing them is meaningful. A shot is
proposed aside when it is far blurrier than the sharpest one, clearly over- or
under-exposed next to the others, or nearly identical to a sharper shot already kept.
The sharpest shot and the shots of protected folders are never proposed: one shot at
least stays. A series is obvious when every shot left is one of those: nothing to judge.
"""

from __future__ import annotations

import statistics
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING, Final

from media_hygiene.plan.likeness import distance

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence

    from media_hygiene.scan.exposure import Exposure

# Mid-gray: an exposure is missed when it lies farther from it than the others.
_MID_GRAY: Final = 127.5


class AsideReason(StrEnum):
    """Why a shot is proposed aside: shown under it, never written in decisions.json."""

    BLURRIER = "blurrier"
    OVEREXPOSED = "overexposed"
    UNDEREXPOSED = "underexposed"
    IDENTICAL = "identical"


@dataclass(frozen=True, slots=True)
class ProposalLimits:
    """`[review]` thresholds; 0 disables a reason."""

    sharpness_below: float = 0.0  # share of the sharpest shot's sharpness
    identical_below: int = 0  # pHash distance to a sharper shot kept
    brightness_gap: float = 0.0  # gray levels from the others' median brightness
    clipped_gap: float = 0.0  # share of clipped pixels above the others' median


@dataclass(frozen=True, slots=True)
class ShotLook:
    """What a shot looks like, and whether it must be kept (sharpest or protected)."""

    sharpness: float
    phash: int
    exposure: Exposure | None = None
    keep: bool = False


@dataclass(frozen=True, slots=True)
class Proposal:
    """A shot proposed aside: the reason, and the rank of the shot it repeats."""

    reason: AsideReason
    like: int | None = None


def propose(
    looks: Sequence[ShotLook], limits: ProposalLimits
) -> Mapping[int, Proposal]:
    """Propose shots of a series aside, the sharpest first compared, then the others.

    Args:
        looks: The shots of the series, by rank.
        limits: The thresholds.

    Returns:
        The proposals, by rank of the shot.
    """
    kept: list[int] = []
    proposals: dict[int, Proposal] = {}
    for rank in sorted(range(len(looks)), key=lambda rank: -looks[rank].sharpness):
        look = looks[rank]
        found = None if look.keep else _reason(rank, looks, limits)
        if found is None and not look.keep:
            found = _repeated(look, [(other, looks[other]) for other in kept], limits)
        if found is None:
            kept.append(rank)
        else:
            proposals[rank] = found
    return proposals


def is_obvious(looks: Sequence[ShotLook], proposals: Mapping[int, Proposal]) -> bool:
    """Tell whether a series needs no judgment: every shot kept had to be.

    Args:
        looks: The shots of the series, by rank.
        proposals: What is proposed aside.

    Returns:
        True when something is proposed and the only shots left are the sharpest and
        those of protected folders.
    """
    return bool(proposals) and all(
        look.keep or rank in proposals for rank, look in enumerate(looks)
    )


def _reason(
    rank: int, looks: Sequence[ShotLook], limits: ProposalLimits
) -> Proposal | None:
    """Find what the shot misses on its own: sharpness, then exposure.

    Args:
        rank: The shot.
        looks: Every shot of the series.
        limits: The thresholds.

    Returns:
        The proposal, or None.
    """
    top = max(look.sharpness for look in looks)
    if top and looks[rank].sharpness / top < limits.sharpness_below:
        return Proposal(AsideReason.BLURRIER)
    others = [
        look.exposure
        for other, look in enumerate(looks)
        if other != rank and look.exposure is not None
    ]
    exposure = looks[rank].exposure
    if exposure is None or not others:
        return None
    return _missed(exposure, others, limits)


def _missed(
    exposure: Exposure, others: Sequence[Exposure], limits: ProposalLimits
) -> Proposal | None:
    """Tell whether an exposure is clearly missed next to the others'.

    Args:
        exposure: The shot's.
        others: The other shots'.
        limits: The thresholds.

    Returns:
        Over- or under-exposed, or None.
    """
    median = statistics.median(other.brightness for other in others)
    gap = exposure.brightness - median
    farther = abs(exposure.brightness - _MID_GRAY) > abs(median - _MID_GRAY)
    if limits.brightness_gap and farther and abs(gap) > limits.brightness_gap:
        return Proposal(
            AsideReason.OVEREXPOSED if gap > 0 else AsideReason.UNDEREXPOSED
        )
    if not limits.clipped_gap:
        return None
    white = statistics.median(other.bright_share for other in others)
    if exposure.bright_share - white > limits.clipped_gap:
        return Proposal(AsideReason.OVEREXPOSED)
    black = statistics.median(other.dark_share for other in others)
    if exposure.dark_share - black > limits.clipped_gap:
        return Proposal(AsideReason.UNDEREXPOSED)
    return None


def _repeated(
    look: ShotLook, kept: Sequence[tuple[int, ShotLook]], limits: ProposalLimits
) -> Proposal | None:
    """Find a sharper shot already kept that this one nearly repeats.

    Args:
        look: The shot.
        kept: The shots kept so far, sharper ones, with their ranks.
        limits: The thresholds.

    Returns:
        The proposal naming that shot, or None.
    """
    for rank, other in kept:
        if distance(look.phash, other.phash) < limits.identical_below:
            return Proposal(AsideReason.IDENTICAL, rank)
    return None
