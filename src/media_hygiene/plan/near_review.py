"""Apply the decisions of `review --near` to the near duplicates a clean moves.

Without a decision, `--tier near` moves the sure groups and `--tier near-all` every
group. A decision overrides that: `planned` moves the copies as the audit planned,
`swap` keeps one of the copies and moves the version the audit kept instead, `none`
moves every version (the kept one last), `leave` moves nothing of the group.
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from enum import StrEnum
from typing import TYPE_CHECKING

from media_hygiene.constants import NearReason

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.scan.models import MediaFile


class NearAction(StrEnum):
    """What a person decided for a group of near duplicates."""

    PLANNED = "planned"  # the copies go, the version the audit kept stays
    SWAP = "swap"  # keep a copy instead, the version the audit kept goes
    LEAVE = "leave"  # nothing of the group moves
    NONE = "none"  # every version goes, the one the audit kept included


@dataclass(frozen=True, slots=True)
class NearVerdict:
    """A decision on one group, in container paths: `keep` for a swap only."""

    action: NearAction
    keep: MediaFile | None = None


@dataclass(frozen=True, slots=True)
class NearSelection:
    """Which groups a clean moves: the tier, then the decisions of the review."""

    every: bool = False  # `--tier near-all`: the groups to check too
    verdicts: Mapping[Path, NearVerdict] | None = None  # by the audit's kept version


def selected(
    groups: Sequence[NearDecision], selection: NearSelection
) -> tuple[NearDecision, ...]:
    """The groups a clean moves, as decided.

    Args:
        groups: Every group of near duplicates and re-encoded videos.
        selection: The tier and the decisions.

    Returns:
        The groups to move, a swapped group with its new kept version; a group
        decided `none` lists its kept version last among the files to move.
    """
    return tuple(_moved(groups, selection))


def _moved(
    groups: Sequence[NearDecision], selection: NearSelection
) -> Iterator[NearDecision]:
    """Yield the groups to move.

    Args:
        groups: Every group.
        selection: The tier and the decisions.

    Yields:
        The groups to move.
    """
    verdicts = selection.verdicts or {}
    for group in groups:
        verdict = verdicts.get(group.keeper.path)
        if verdict is None:
            if selection.every or group.sure is not None:
                yield group
        elif verdict.action is NearAction.PLANNED:
            yield group
        elif verdict.action is NearAction.SWAP and verdict.keep is not None:
            yield swapped(group, verdict.keep)
        elif verdict.action is NearAction.NONE:
            yield replace(group, removable=(*group.removable, group.keeper))


def swapped(group: NearDecision, keep: MediaFile) -> NearDecision:
    """Keep one of the copies instead of the version the audit kept.

    Args:
        group: The group, as planned.
        keep: The copy to keep.

    Returns:
        The group, `keep` kept, the other versions to move.
    """
    others = (group.keeper, *(file for file in group.removable if file != keep))
    return replace(
        group,
        keeper=keep,
        removable=others,
        same_stream=frozenset(),
        reason=NearReason.CHOSEN,
        rule=None,
    )
