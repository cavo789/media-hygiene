"""The moves of a clean chosen by a tier or a person: near, burst shots, files chosen.

None of them is an identical copy: each goes to the quarantine (never deleted), where
`undo` finds it, and only while it is still the very file the audit, the review or
the search saw.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.actions.journaled import Origin
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.outcome import Incident
from media_hygiene.actions.verify import burst_blocker, chosen_blocker, near_blocker

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.actions.clean_step import CleanLabels, Planned
    from media_hygiene.actions.journaled import JournaledChanges
    from media_hygiene.actions.outcome import Tally
    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.plan.similar_models import BurstChoice, NearDecision
    from media_hygiene.scan.models import MediaFile


class AsideMoves:
    """Moves near duplicates, burst shots and chosen files to the quarantine."""

    def __init__(
        self, changes: JournaledChanges, tally: Tally, labels: CleanLabels
    ) -> None:
        """Act through the run's journal and counts.

        Args:
            changes: The journaled changes of the run.
            tally: Where a file left alone is counted, with its reason.
            labels: What the screen says of each file.
        """
        self._changes = changes
        self._tally = tally
        self._labels = labels

    def planned(self, plan: CleanPlan) -> Iterator[Planned]:
        """List the moves, in the order they must happen.

        Args:
            plan: What to clean.

        Yields:
            Each file, what the screen says of it, and its move to the quarantine.
        """
        for near in plan.near:
            for file in near.removable:
                yield file, self._labels.near, partial(self._near, near, file)
        for choice in plan.bursts:
            for file in choice.discarded:
                yield file, self._labels.burst, partial(self._burst, choice, file)
        for file in plan.chosen:
            yield file, self._labels.chosen, partial(self._chosen, file)

    def _near(self, decision: NearDecision, file: MediaFile) -> None:
        """Move one near duplicate to the quarantine.

        Args:
            decision: The near-duplicate decision, holding the kept picture.
            file: Copy to move.
        """
        blocker = near_blocker(decision.keeper.path, file)
        if blocker is not None:
            self._tally.skipped.append(Incident(file.path, blocker))
            return
        keeper = Origin(decision.keeper.path)
        self._changes.quarantine(file, ActionKind.QUARANTINE_NEAR, keeper)

    def _burst(self, choice: BurstChoice, file: MediaFile) -> None:
        """Move one burst shot a review set aside to the quarantine.

        A series set aside whole has no kept shot to name in the journal.

        Args:
            choice: The review of its series, holding the shots kept.
            file: Shot to move.
        """
        blocker = burst_blocker(choice.kept, file)
        if blocker is not None:
            self._tally.skipped.append(Incident(file.path, blocker))
            return
        keeper = Origin(choice.kept[0].path if choice.kept else None)
        self._changes.quarantine(file, ActionKind.QUARANTINE_BURST, keeper)

    def _chosen(self, file: MediaFile) -> None:
        """Move one file set aside in `search` to the quarantine.

        Args:
            file: The file, as the index knew it when it was chosen.
        """
        blocker = chosen_blocker(file)
        if blocker is not None:
            self._tally.skipped.append(Incident(file.path, blocker))
            return
        self._changes.quarantine(file, ActionKind.QUARANTINE_CHOSEN)
