"""A `review --near` in progress: the decided groups, saved after every decision.

The decisions file is shared with the report's pairs and the burst review: this review
keeps what it finds there and writes its own `near` key, the decided groups only.
Reopened on the same folders, it resumes where it stopped; a decided group that
changed since is dropped, to decide again.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.plan.near_review import NearAction
from media_hygiene.report.decisions import write_decisions
from media_hygiene.review.keyed_choices import RankedSession, record, with_actions
from media_hygiene.review.near_file import (
    decision_key,
    group_decision,
    group_key,
    near_proven,
    read_near_back,
)
from media_hygiene.review.near_views import NearReviewState
from media_hygiene.review.views import preview_key

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.plan.similar_models import NearDecision
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.review.near_file import NearProof
    from media_hygiene.review.near_views import GroupState, NearStateBuilder
    from media_hygiene.review.place import DecisionsPlace


@dataclass(frozen=True, slots=True)
class NearSource:
    """What the review is about: the groups, how to show them, the file to write."""

    groups: tuple[NearDecision, ...]
    builder: NearStateBuilder
    target: Path
    place: DecisionsPlace


class NearSession(RankedSession[NearAction]):
    """The groups under review and the decisions, in memory and on disk."""

    _source: NearSource
    _states: tuple[GroupState, ...]

    def __init__(self, source: NearSource, base: DecisionsFile) -> None:
        """Resume the decisions of `base` that still match a group of the audit.

        Args:
            source: The groups and the decisions file.
            base: What the decisions file holds already.
        """
        self._source = source
        self._base = base
        mapper = source.builder.mapper
        self._states = tuple(source.builder.group(group) for group in source.groups)
        self._keys = {
            group_key(mapper, group): rank for rank, group in enumerate(source.groups)
        }
        self._previews = {
            preview_key(file): file.path
            for group in source.groups
            for file in (group.keeper, *group.removable, *group.protected)
        }
        self._actions: dict[int, NearAction] = {}
        self.dropped = 0
        for decision in base.near:
            rank = self._keys.get(decision_key(decision))
            same = rank is not None and decision == group_decision(
                mapper, source.groups[rank], decision.action
            )
            if rank is None or not same or self.problem(rank, decision.action):
                self.dropped += 1
                continue
            self._actions[rank] = decision.action

    def state(self) -> NearReviewState:
        """Describe every group and the decisions so far, for the page.

        Returns:
            The state.
        """
        return NearReviewState(
            decisions_file=self.place.argument,
            decisions_place=self.place.host,
            groups=with_actions(self._states, self._actions),
        )

    def preview_source(self, key: str) -> Path | None:
        """Find the version a preview or an original shows.

        Args:
            key: The preview key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        return self._previews.get(key)

    def problem(self, rank: int, action: NearAction | None) -> str | None:
        """Explain why a decision cannot be made on a group, or return None.

        Args:
            rank: Rank of the group.
            action: The decision (None: back to undecided).

        Returns:
            The translated reason, or None.
        """
        if not 0 <= rank < len(self._states):
            return _("There is no such group.")
        state = self._states[rank]
        if action is NearAction.SWAP and not state.swappable:
            message = _("{path} is in a protected folder: it is never moved.")
            keeper = self._source.groups[rank].keeper.path
            return message.format(path=self._source.builder.mapper.to_host(keeper))
        return None

    def save(self) -> None:
        """Write the decisions file: the decided groups, in the audit's order."""
        write_decisions(self._source.target, self.decisions())

    def on_disk(self) -> NearProof:
        """Read the decisions file back from the disk.

        Returns:
            What it holds, group by group.
        """
        return read_near_back(self._source.target, self._keys)

    def decide(self, choices: Mapping[int, NearAction | None]) -> NearProof:
        """Record choices, save them in one write, then read the file back.

        Args:
            choices: The decision by group rank (None: back to undecided).

        Returns:
            Those groups, as the file read back from the disk holds them.

        Raises:
            DecisionsError: An unknown group, a swap that would move a file of a
                protected folder, or a file that does not hold the choices once saved.
        """
        record(self._actions, choices, self.problem)
        self.save()
        return near_proven(self.on_disk(), choices)

    def decisions(self) -> DecisionsFile:
        """Build the decisions file: what it held, the decided groups in order.

        Returns:
            The decisions, in host paths.
        """
        mapper, groups = self._source.builder.mapper, self._source.groups
        listed = tuple(
            group_decision(mapper, groups[rank], self._actions[rank])
            for rank in sorted(self._actions)
        )
        return self._base.model_copy(update={"near": listed})
