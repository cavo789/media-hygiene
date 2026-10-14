"""Execute a plan: quarantine copies (deleted with `--delete`), delete empty files."""

from __future__ import annotations

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.actions.clean_step import clean_labels, clean_step
from media_hygiene.actions.journaled import JournaledChanges, Origin
from media_hygiene.actions.kinds import ActionKind
from media_hygiene.actions.outcome import Incident, Outcome, Tally
from media_hygiene.actions.parallel import (
    Runner,
    guarded,
    run_all,
    shown_on,
    stopping_on,
)
from media_hygiene.actions.verify import (
    burst_blocker,
    change_blocker,
    checked_removal,
    near_blocker,
    orphan_blocker,
)
from media_hygiene.constants import BrokenReason, MediaKind

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.actions.clean_step import Planned
    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.plan.models import CleanPlan, KeepDecision
    from media_hygiene.plan.similar_models import BurstChoice, NearDecision
    from media_hygiene.scan.models import BrokenFile, MediaFile


class CleanExecutor:
    """Acts on a few files at a time; a problem on one file never stops the others."""

    def __init__(self, context: CleanContext) -> None:
        """Prepare a run.

        Args:
            context: Journal, path mapper, quarantine folder and progress sink.
        """
        self._context = context
        self._tally = Tally()
        self._changes = JournaledChanges(context, self._tally)
        self._labels = clean_labels(delete_copies=context.delete_copies)

    def run(self, plan: CleanPlan) -> Outcome:
        """Execute every action of the plan.

        Args:
            plan: What to clean.

        Returns:
            What was done, skipped and why.
        """
        actions = list(self._actions(plan))
        orphans = [
            (file, self._labels.orphan, partial(self._quarantine_orphan, file))
            for file in plan.orphans
        ]
        step = clean_step(
            [*actions, *orphans], delete_copies=self._context.delete_copies
        )
        self._context.progress.start(step, len(actions) + len(orphans))
        context = self._context
        runner = Runner(
            guarded(self._tally), shown_on(context), stopping=stopping_on(context)
        )
        run_all(actions, runner)
        # Last, one by one: a sidecar is an orphan only once its files are gone.
        run_all(orphans, replace(runner, workers=1))
        self._context.progress.stop()
        return self._tally.freeze()

    def _actions(self, plan: CleanPlan) -> Iterator[Planned]:
        """List the actions of the plan, in the order they must happen.

        Args:
            plan: What to clean.

        Yields:
            Each file, what the screen says of it, and the action on it.
        """
        for decision in plan.decisions:
            for file in decision.removable:
                action = partial(self._delete_copy, decision, file)
                yield file, self._labels.of_copy(file), action
        yield from self._look_alikes(plan)
        for item in plan.broken:
            action = partial(self._handle_broken, item)
            yield item.file, self._labels.of_broken(item), action

    def _look_alikes(self, plan: CleanPlan) -> Iterator[Planned]:
        """List the moves of pictures that look like a kept one: near, burst shots.

        Args:
            plan: What to clean.

        Yields:
            Each file, what the screen says of it, and its move to the quarantine.
        """
        for near in plan.near:
            for file in near.removable:
                action = partial(self._quarantine_near, near, file)
                yield file, self._labels.near, action
        for choice in plan.bursts:
            for file in choice.discarded:
                action = partial(self._quarantine_burst, choice, file)
                yield file, self._labels.burst, action

    def _delete_copy(self, decision: KeepDecision, file: MediaFile) -> None:
        """Set aside one duplicate copy after a byte-for-byte check against the keeper.

        It goes to the quarantine; with `--delete`, a media copy is deleted for good
        (a copy of another file than a media always goes to the quarantine).

        Args:
            decision: The group decision, holding the keeper.
            file: Copy to delete.
        """
        keeper = decision.keeper.path
        removal = checked_removal(keeper, file.path, decision.size)
        if removal.reason is not None:
            self._tally.skipped.append(Incident(file.path, removal.reason))
            return
        if file.kind is MediaKind.OTHER or not self._context.delete_copies:
            origin = Origin(keeper, removal.sha256)
            self._changes.quarantine(file, ActionKind.QUARANTINE_DUPLICATE, origin)
            return
        entry = self._changes.entry(file, ActionKind.DELETE_DUPLICATE).model_copy(
            update={"sha256": decision.digest, "keeper": str(decision.keeper.path)},
        )
        self._changes.act(entry, file.path.unlink)

    def _quarantine_near(self, decision: NearDecision, file: MediaFile) -> None:
        """Move one near duplicate to the quarantine, where `undo` finds it again.

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

    def _quarantine_burst(self, choice: BurstChoice, file: MediaFile) -> None:
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

    def _handle_broken(self, item: BrokenFile) -> None:
        """Delete an empty file, or move an unreadable one to the quarantine.

        Args:
            item: The broken file.
        """
        blocker = change_blocker(item.file)
        if blocker is not None:
            self._tally.skipped.append(Incident(item.file.path, blocker))
            return
        if item.reason is BrokenReason.EMPTY:
            entry = self._changes.entry(item.file, ActionKind.DELETE_EMPTY)
            self._changes.act(entry, item.file.path.unlink)
            return
        self._changes.quarantine(item.file, ActionKind.QUARANTINE)

    def _quarantine_orphan(self, sidecar: MediaFile) -> None:
        """Move an orphan sidecar to the quarantine, where `undo` finds it again.

        Args:
            sidecar: The sidecar, as audited.
        """
        blocker = orphan_blocker(sidecar)
        if blocker is not None:
            self._tally.skipped.append(Incident(sidecar.path, blocker))
            return
        self._changes.quarantine(sidecar, ActionKind.QUARANTINE_SIDECAR)
