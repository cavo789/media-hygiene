"""A `review --pairs` in progress: the decided folder pairs, saved after every choice.

The decisions file is shared with the other reviews and `search`: this one keeps what
it finds there and writes the `pairs` key (the report's download writes it too).
Reopened on the same folders, it resumes; a pair that no longer exists is dropped.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.plan.review import PairAction
from media_hygiene.report.decisions import write_decisions
from media_hygiene.report.pair_views import pair_samples
from media_hygiene.review.keyed_choices import RankedSession, record, with_actions
from media_hygiene.review.pairs_file import (
    pair_decision,
    pair_key,
    pairs_proven,
    read_pairs_back,
)
from media_hygiene.review.pairs_views import PairsReviewState
from media_hygiene.review.views import preview_key

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.plan.pairs import FolderPair
    from media_hygiene.report.decisions import DecisionsFile
    from media_hygiene.review.pairs_file import PairsProof
    from media_hygiene.review.pairs_views import PairsStateBuilder, PairState
    from media_hygiene.review.place import DecisionsPlace


@dataclass(frozen=True, slots=True)
class PairsSource:
    """What the review is about: the pairs, how to show them, the file to write."""

    pairs: tuple[FolderPair, ...]
    builder: PairsStateBuilder
    target: Path
    place: DecisionsPlace


class PairsSession(RankedSession[PairAction]):
    """The folder pairs under review and the decisions, in memory and on disk."""

    _source: PairsSource
    _states: tuple[PairState, ...]

    def __init__(self, source: PairsSource, base: DecisionsFile) -> None:
        """Resume the decisions of `base` that still match a pair of the audit.

        Args:
            source: The pairs and the decisions file.
            base: What the decisions file holds already.
        """
        self._source = source
        self._base = base
        builder = source.builder
        self._states = tuple(builder.pair(pair) for pair in source.pairs)
        self._keys = {
            pair_key(builder.mapper, p): r for r, p in enumerate(source.pairs)
        }
        self._previews = {
            preview_key(file): file.path
            for pair in source.pairs
            for file in pair_samples(pair)
        }
        self._actions: dict[int, PairAction] = {}
        self.dropped = 0
        for decision in base.pairs:
            rank = self._keys.get((decision.kept_in, decision.removed_from))
            if rank is None or self.problem(rank, decision.action):
                self.dropped += 1
                continue
            self._actions[rank] = decision.action

    def state(self) -> PairsReviewState:
        """Describe every pair and the decisions so far, for the page.

        Returns:
            The state.
        """
        return PairsReviewState(
            decisions_file=self.place.argument,
            decisions_place=self.place.host,
            pairs=with_actions(self._states, self._actions),
        )

    def preview_source(self, key: str) -> Path | None:
        """Find the file a preview or an original shows.

        Args:
            key: The preview key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        return self._previews.get(key)

    def problem(self, rank: int, action: PairAction | None) -> str | None:
        """Explain why a decision cannot be made on a pair, or return None.

        Args:
            rank: Rank of the pair.
            action: The decision (None: back to undecided).

        Returns:
            The translated reason, or None.
        """
        if not 0 <= rank < len(self._states):
            return _("There is no such folder pair.")
        state = self._states[rank]
        if action is PairAction.SWAP and not state.swappable:
            message = _(
                "{folder} is protected, or the copies lie in one folder: the pair "
                "cannot be swapped."
            )
            return message.format(folder=state.kept_in)
        return None

    def save(self) -> None:
        """Write the decisions file: the decided pairs, in the audit's order."""
        write_decisions(self._source.target, self.decisions())

    def on_disk(self) -> PairsProof:
        """Read the decisions file back from the disk.

        Returns:
            What it holds, pair by pair.
        """
        return read_pairs_back(self._source.target, self._keys)

    def decide(self, choices: Mapping[int, PairAction | None]) -> PairsProof:
        """Record choices, save them in one write, then read the file back.

        Args:
            choices: The decision by pair rank (None: back to undecided).

        Returns:
            Those pairs, as the file read back from the disk holds them.

        Raises:
            DecisionsError: An unknown pair, a swap that is not allowed, or a file
                that does not hold the choices once saved.
        """
        record(self._actions, choices, self.problem)
        self.save()
        return pairs_proven(self.on_disk(), choices)

    def decisions(self) -> DecisionsFile:
        """Build the decisions file: what it held, the decided pairs in order.

        Returns:
            The decisions, in host paths.
        """
        keys = {rank: key for key, rank in self._keys.items()}
        listed = tuple(
            pair_decision(keys[rank], self._actions[rank])
            for rank in sorted(self._actions)
        )
        return self._base.model_copy(update={"pairs": listed})
