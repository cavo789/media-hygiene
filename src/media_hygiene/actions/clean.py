"""Execute a plan: quarantine copies (deleted with `--delete`), delete empty files.

The copies of a pair keeping both names become hard links (`clean_links`, 0213).
What is moved because a person or the tier chose so (near duplicates, burst shots,
files chosen in `search`) is planned by `clean_aside`.
"""

from __future__ import annotations

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.actions.clean_aside import AsideMoves
from media_hygiene.actions.clean_gone import mark_gone
from media_hygiene.actions.clean_leftovers import Leftovers
from media_hygiene.actions.clean_links import CopyLinker
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
from media_hygiene.actions.sort_cleanup import FolderCleaner
from media_hygiene.actions.verify import checked_removal
from media_hygiene.plan.pair_links import linked_count

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.actions.clean_folders import EmptiedFolders
    from media_hygiene.actions.clean_step import Planned
    from media_hygiene.actions.journaled import CleanContext
    from media_hygiene.plan.models import CleanPlan, KeepDecision
    from media_hygiene.scan.models import MediaFile


class CleanExecutor:
    """Acts on a few files at a time; a problem on one file never stops the others."""

    def __init__(
        self, context: CleanContext, folders: EmptiedFolders | None = None
    ) -> None:
        """Prepare a run.

        Args:
            context: Journal, path mapper, quarantine folder and progress sink.
            folders: The folders it may leave empty, removed last (0202).
        """
        self._context = context
        self._folders = folders
        self._tally = Tally()
        self._changes = JournaledChanges(context, self._tally)
        self._leftovers = Leftovers(self._changes, self._tally)
        self._linker = CopyLinker(self._changes, self._tally)
        self._labels = clean_labels(delete_copies=context.delete_copies)

    def run(self, plan: CleanPlan) -> Outcome:
        """Execute the plan: copies first, then what may be their keeper (a shot).

        The folders left empty go last, in the same journal: `undo` recreates them
        before it puts the files back. Ctrl+C stops the run before them.

        Args:
            plan: What to clean.

        Returns:
            What was done, skipped and why.
        """
        actions = list(self._actions(plan))
        orphans = [
            (file, self._labels.orphan, partial(self._leftovers.orphan, file))
            for file in plan.orphans
        ]
        step = clean_step(
            [*actions, *orphans], delete_copies=self._context.delete_copies
        )
        self._context.progress.start(step, len(actions) + len(orphans))
        runner = Runner(
            guarded(self._tally),
            shown_on(self._context),
            self._context.workers,
            stopping=stopping_on(self._context.progress),
        )
        copies = plan.removable_count + linked_count(plan)
        run_all(actions[:copies], runner)
        run_all(actions[copies:], runner)
        # Last, one by one: a sidecar is an orphan only once its files are gone.
        run_all(orphans, replace(runner, workers=1))
        mark_gone(self._changes, plan)  # no file moves: journal lines only (0224)
        self._context.progress.stop()
        if self._folders is not None and self._folders.candidates:
            cleaner = FolderCleaner(self._changes, self._tally)
            found = cleaner.run(list(self._folders.candidates), self._folders.rules)
            self._tally.folders_removed = found.removed
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
                yield file, self._labels.copy, action
            for file in decision.linked:  # a pair keeping both names (0213)
                action = partial(self._linker.link, decision, file)
                yield file, self._labels.linked, action
        yield from AsideMoves(self._changes, self._tally, self._labels).planned(plan)
        for item in plan.broken:
            action = partial(self._leftovers.broken, item)
            yield item.file, self._labels.of_broken(item), action

    def _delete_copy(self, decision: KeepDecision, file: MediaFile) -> None:
        """Set aside one duplicate copy after a byte-for-byte check against the keeper.

        It goes to the quarantine; with `--delete`, it is deleted for good.

        Args:
            decision: The group decision, holding the keeper.
            file: Copy to delete.
        """
        keeper = decision.keeper.path
        removal = checked_removal(keeper, file.path, decision.size)
        if removal.reason is not None:
            self._tally.skipped.append(Incident(file.path, removal.reason))
            return
        if not self._context.delete_copies:
            origin = Origin(keeper, removal.sha256)
            self._changes.quarantine(file, ActionKind.QUARANTINE_DUPLICATE, origin)
            return
        entry = self._changes.entry(file, ActionKind.DELETE_DUPLICATE).model_copy(
            update={"sha256": decision.digest, "keeper": str(decision.keeper.path)},
        )
        self._changes.act(entry, file.path.unlink)
