"""Near duplicates found in rounds, so that cleaning them leaves none behind.

Alike files are linked step by step: A looks like B, B like C, while A and C are too
far apart, or differ by their date. The version kept for such a group only takes the
copies near itself. The rest of the group is grouped again on its own, without the
version kept and its copies: two copies of another take are compared together. And
once the copies are gone, a chain may break: each round runs again on the files the
previous rounds leave, until a round finds nothing. One audit finds what successive
audit-and-clean runs would.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.plan.similar_models import NearDecision

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable, Sequence
    from pathlib import Path

    from media_hygiene.plan.keeper import KeepPolicy
    from media_hygiene.plan.near_keeper import NearChoice
    from media_hygiene.scan.models import MediaFile


@dataclass(frozen=True, slots=True)
class Grouping:
    """How alike files are linked, and how one group is settled."""

    # The linked sets of two files or more, among some files (their order kept).
    clusters: Callable[[Sequence[MediaFile]], Iterable[list[MediaFile]]]
    # The version kept in a group, and the copies near it.
    settle: Callable[[list[MediaFile]], tuple[NearChoice, list[MediaFile]]]
    policy: KeepPolicy


def in_rounds(
    files: Sequence[MediaFile], grouping: Grouping
) -> tuple[NearDecision, ...]:
    """Decide again on the files left until no new copy turns up.

    Every decision lists at least one removable copy, so each round removes files and
    the loop ends.

    Args:
        files: Candidate files.
        grouping: How they are linked and settled.

    Returns:
        The decisions of every round, one per keeper, the largest keeper first.
    """
    decisions: list[NearDecision] = []
    remaining = list(files)
    while found := _round(remaining, grouping):
        decisions.extend(found)
        gone = {file.path for decision in found for file in decision.removable}
        remaining = [file for file in remaining if file.path not in gone]
    merged = _merged(decisions)
    return tuple(sorted(merged, key=lambda d: (-d.keeper.size, str(d.keeper.path))))


def _round(files: Sequence[MediaFile], grouping: Grouping) -> list[NearDecision]:
    """Settle every group, then what each group leaves, grouped again.

    Args:
        files: Candidate files.
        grouping: How they are linked and settled.

    Returns:
        The decisions of this round.
    """
    decisions: list[NearDecision] = []
    pending = list(grouping.clusters(files))
    while pending:
        cluster = pending.pop()
        choice, near = grouping.settle(cluster)
        if decision := _decision(choice, near, grouping.policy):
            decisions.append(decision)
        settled = {choice.keeper.path, *(file.path for file in near)}
        left = [file for file in cluster if file.path not in settled]
        pending.extend(grouping.clusters(left))
    return decisions


def _decision(
    choice: NearChoice, near: Sequence[MediaFile], policy: KeepPolicy
) -> NearDecision | None:
    """Turn the version kept and its near copies into a decision.

    Args:
        choice: The version kept and why.
        near: The copies near it.
        policy: Protected folders: their copies are never removable.

    Returns:
        The decision, or None when every copy is protected.
    """
    removable = tuple(file for file in near if not policy.is_protected(file))
    if not removable:
        return None
    protected = tuple(file for file in near if policy.is_protected(file))
    return NearDecision(
        choice.keeper, removable, protected, reason=choice.reason, rule=choice.rule
    )


def _merged(decisions: Iterable[NearDecision]) -> list[NearDecision]:
    """Join the decisions of one keeper found in different rounds.

    Args:
        decisions: The decisions, in the order found.

    Returns:
        One decision per keeper, the reason of its first round; a protected copy,
        never removed, is listed once.
    """
    by_keeper: dict[Path, NearDecision] = {}
    for decision in decisions:
        first = by_keeper.setdefault(decision.keeper.path, decision)
        if first is not decision:
            protected = dict.fromkeys((*first.protected, *decision.protected))
            by_keeper[decision.keeper.path] = replace(
                first,
                removable=(*first.removable, *decision.removable),
                protected=tuple(protected),
            )
    return list(by_keeper.values())
