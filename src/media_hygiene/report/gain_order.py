"""Near duplicates in the order that frees the most space soonest, with a running total.

A few re-encoded videos often weigh more than hundreds of shrunk photos: a person short
of time gets most of the space back by looking at the first groups. The groups to check
come first, then the sure ones; each list by the space its copies free, largest first.
Each group carries the share of the space freed by it and every group above it.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.plan.similar_models import NearDecision

_PERCENT: Final = 100


def gain_order(groups: Sequence[NearDecision]) -> tuple[tuple[NearDecision, int], ...]:
    """Order the groups, the largest space first, each with its running share.

    Args:
        groups: The groups, as the audit found them.

    Returns:
        Each group and the share of the space, in percent, that it and the groups
        before it free; ties keep the audit's order.
    """
    ordered = sorted(
        groups, key=lambda group: (group.sure is not None, -group.reclaimable)
    )
    return tuple(
        zip(ordered, running_shares([g.reclaimable for g in ordered]), strict=True)
    )


def running_shares(gains: Sequence[int]) -> tuple[int, ...]:
    """The running total of gains, as shares of their sum.

    Args:
        gains: The bytes each group frees, in the order shown.

    Returns:
        For each group, the percentage freed by it and those before it (100 when
        nothing is freed at all).
    """
    total = sum(gains)
    shares: list[int] = []
    running = 0
    for gain in gains:
        running += gain
        shares.append(round(_PERCENT * running / total) if total else _PERCENT)
    return tuple(shares)
