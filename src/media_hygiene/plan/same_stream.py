"""Re-encoded videos that were not re-encoded: the same picture and sound, new metadata.

A copy whose metadata only was rewritten (a rating set in Windows, a tag) is a little
larger or smaller than its original for no reason that matters: the size says nothing
about its quality. Between such copies, the usual keep rules choose, as for identical
files: a protected or preferred folder, a name or a folder someone chose.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.plan.near_keeper import rules_choice
from media_hygiene.plan.similar_models import NearDecision

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy

# The keeper and at least one copy.
_PAIR: Final = 2


def with_same_streams(
    decisions: tuple[NearDecision, ...],
    streams: Mapping[Path, str],
    policy: KeepPolicy,
) -> tuple[NearDecision, ...]:
    """Choose again, by the usual rules, between copies of the same picture and sound.

    Args:
        decisions: The re-encoded video groups, kept by resolution then size.
        streams: The digest of the picture and sound of the videos hashed.
        policy: Protected folders and the usual keep rules.

    Returns:
        The groups, a copy with nothing left to move dropped.
    """
    chosen = (_rekeep(decision, streams, policy) for decision in decisions)
    return tuple(decision for decision in chosen if decision.removable)


def _rekeep(
    decision: NearDecision, streams: Mapping[Path, str], policy: KeepPolicy
) -> NearDecision:
    """Keep, among the copies of the keeper's very picture and sound, the usual choice.

    Args:
        decision: A re-encoded video group.
        streams: The digest of the picture and sound of the videos hashed.
        policy: Protected folders and the usual keep rules.

    Returns:
        The group, unchanged when no copy shares the keeper's picture and sound.
    """
    stream = streams.get(decision.keeper.path)
    members = (decision.keeper, *decision.removable, *decision.protected)
    same = [file for file in members if stream and streams.get(file.path) == stream]
    if len(same) < _PAIR:
        return decision
    choice = rules_choice(same, policy)
    keeper = choice.keeper
    others = [file for file in members if file != keeper]
    return NearDecision(
        keeper,
        tuple(file for file in others if not policy.is_protected(file)),
        tuple(file for file in others if policy.is_protected(file)),
        frozenset(file.path for file in same if file != keeper),
        reason=choice.reason,
        rule=choice.rule,
    )
