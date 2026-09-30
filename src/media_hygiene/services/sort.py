"""The sort use case: apply the edited plan of `classify`, journaled, and prove it.

Nothing moves unless every change can be journaled and undone (`ensure_ready`) and
every destination is safe (`prepare`). The files are counted before and after, and
every move is checked (`actions/manifest.py`).
"""

from __future__ import annotations

from dataclasses import dataclass, replace
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalWriter, journal_file
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.manifest import Manifest, census, verify_moves
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.runs import new_run_id
from media_hygiene.actions.sort import SortExecutor
from media_hygiene.actions.sort_build import PlanContext, sort_plan
from media_hygiene.actions.sort_cleanup import FolderCleaner
from media_hygiene.actions.sort_folders import FolderReport, candidates, verdicts
from media_hygiene.actions.sort_moves import SortContext
from media_hygiene.actions.sort_resume import moved_rows
from media_hygiene.classify.workbook.edits import resolve
from media_hygiene.errors import MountError
from media_hygiene.index.repository import FactsRepository
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.sort_guards import check_companions, check_destinations
from media_hygiene.services.sort_report import (
    folder_rules,
    source_roots,
    write_manifest,
)

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.actions.sort import MoveOutcome
    from media_hygiene.actions.sort_folders import FolderRules
    from media_hygiene.actions.sort_plan import SortPlan
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.services.sort_inputs import SortInputs


@dataclass(frozen=True, slots=True)
class Prepared:
    """A sort ready to run: its moves, and the folders it would remove."""

    inputs: SortInputs
    plan: SortPlan
    rules: FolderRules
    candidates: tuple[Path, ...]  # folders that may end up empty, deepest first
    folders: FolderReport  # the prediction


@dataclass(frozen=True, slots=True)
class SortResult:
    """What a sort run did, and the proof that nothing was lost."""

    run_id: str
    moves: MoveOutcome
    folders: FolderReport
    manifest: Manifest
    manifest_file: Path | MountError | None  # None: no /reports mount


class SortService:
    """Refuses to act unless every move can be journaled, undone and verified."""

    def __init__(self, runtime: Runtime, progress: ProgressSink) -> None:
        """Prepare a sort.

        Args:
            runtime: Settings, mount points and output.
            progress: Where to report progress.
        """
        self._runtime = runtime
        self._progress = progress

    def ensure_ready(self) -> None:
        """Check, before reading anything, that sorting is possible and reversible."""
        ensure_can_act(self._runtime, "sort")

    def prepare(self, inputs: SortInputs, *, keep_empty: bool = False) -> Prepared:
        """Apply the edits, drop what earlier runs moved, check every destination.

        Args:
            inputs: The plan and its edits.
            keep_empty: `--keep-empty-folders`: no folder is removed.

        Returns:
            The sort, ready to run.
        """
        runtime = self._runtime
        plan_id = inputs.plan.plan_id
        protected = runtime.settings.folders.protected
        context = PlanContext(
            runtime.mapper,
            tuple(runtime.mapper.to_container(path) for path in protected),
            moved_rows(runtime.locations.journal_dir, plan_id),
        )
        plan = sort_plan(plan_id, resolve(inputs.plan, inputs.edits), context)
        check_companions(plan)
        check_destinations(runtime, plan)
        rules = folder_rules(runtime, inputs.plan)
        sources = [move.source for move in plan.moves] + list(plan.moved_before)
        found = () if keep_empty else tuple(candidates(sources, rules))
        gone = [move.source for move in plan.moves]
        predicted = FolderReport.of(verdicts(list(found), rules, gone))
        return Prepared(inputs, plan, rules, found, predicted)

    def execute(self, prepared: Prepared, stop: Callable[[], bool]) -> SortResult:
        """Move the files under a new run identifier, then prove nothing was lost.

        Args:
            prepared: The sort.
            stop: Tells when Ctrl+C was pressed: the run stops between two files.

        Returns:
            The run, what it did, and its manifest.
        """
        runtime = self._runtime
        journal_dir = runtime.locations.journal_dir
        journal_dir.mkdir(parents=True, exist_ok=True)
        run_id = new_run_id(journal_dir)
        roots = (*source_roots(runtime, prepared.plan), *prepared.plan.roots)
        before = census(roots, prepared.rules.junk)
        moves, folders = self._act(prepared, run_id, stop)
        self._follow(moves.moved)
        verified, problems = verify_moves(moves.moved, runtime.mapper.to_host)
        manifest = Manifest(
            run_id=run_id,
            plan_id=prepared.plan.plan_id,
            roots=tuple(runtime.mapper.to_host(root) for root in sorted(set(roots))),
            before=before,
            after=census(roots, prepared.rules.junk),
            moved=len(moves.moved),
            verified=verified,
            problems=problems,
        )
        try:
            written: Path | MountError | None = write_manifest(runtime, manifest)
        except MountError as exc:  # the moves are over: only a warning
            written = exc
        return SortResult(run_id, moves, folders, manifest, written)

    def _act(
        self, prepared: Prepared, run_id: str, stop: Callable[[], bool]
    ) -> tuple[MoveOutcome, FolderReport]:
        """Move the files, then remove the folders left empty, in one journal.

        Args:
            prepared: The sort.
            run_id: The run.
            stop: Tells when Ctrl+C was pressed.

        Returns:
            What the moves did (the folders' changes counted too), the folders.
        """
        locations, plan = self._runtime.locations, prepared.plan
        tally = Tally()
        with JournalWriter.open(journal_file(locations.journal_dir, run_id)) as journal:
            changes = CleanContext(
                journal,
                self._runtime.mapper,
                locations.quarantine_dir / run_id,
                self._progress,
                Phase.SORT,
            )
            executor = SortExecutor(SortContext(changes, plan.plan_id, stop), tally)
            moves = executor.run(plan)
            folders = FolderReport()
            if not moves.interrupted and prepared.candidates:
                cleaner = FolderCleaner(executor.relocator.changes, tally)
                folders = cleaner.run(list(prepared.candidates), prepared.rules)
        return replace(moves, outcome=tally.freeze()), folders

    def _follow(self, moved: tuple[JournalEntry, ...]) -> None:
        """Update the index: the files moved keep their digests and facts.

        Args:
            moved: The moves done.
        """
        index = self._runtime.index_file
        if index is None or not moved:
            return
        with FactsRepository.open(index) as repository:
            repository.move((entry.path, entry.target or entry.path) for entry in moved)
