"""The runs of one sort: a sort stopped then resumed is several runs of one plan."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import (
    done_states,
    journal_file,
    latest_states,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.actions.runs import list_run_ids, run_phase

if TYPE_CHECKING:
    from datetime import datetime
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry


@dataclass(frozen=True, slots=True)
class PlanRun:
    """One sort run of a plan, still to undo: when it ran, how many files it moved."""

    run_id: str
    started: datetime
    moved: int


@dataclass(frozen=True, slots=True)
class PlanRuns:
    """What `undo` of a sort run reverses: every run of its plan not undone yet.

    Attributes:
        named: The run the user named (or the latest one).
        runs: The runs to undo, newest first; the named run alone when it has no plan.
        undone: The runs of the plan already undone, left aside.
    """

    named: str
    runs: tuple[PlanRun, ...]
    undone: tuple[str, ...]

    @property
    def later(self) -> str | None:
        """The newest run to undo when it came after the named one, else None.

        Returns:
            Its identifier, or None.
        """
        newest = self.runs[0].run_id if self.runs else self.named
        return newest if newest > self.named else None

    @property
    def together(self) -> bool:
        """Tell whether more than the named run is undone (the user must know).

        Returns:
            True when the list is not just the named run.
        """
        return [run.run_id for run in self.runs] != [self.named]


def plan_of(entries: list[JournalEntry]) -> str | None:
    """Tell which classify plan a sort run applied.

    Args:
        entries: The run's journal.

    Returns:
        The plan id its moves carry, or None (not a sort, or nothing moved).
    """
    return next((entry.plan for entry in entries if entry.plan), None)


def runs_of_plan(journal_dir: Path, run_id: str) -> PlanRuns:
    """Collect the sort runs sharing the plan of a run, newest first.

    Args:
        journal_dir: Journal mount point.
        run_id: The run named; a sort run.

    Returns:
        The runs to undo together, and those of the plan already undone.
    """
    named = read_journal(journal_file(journal_dir, run_id))
    plan = plan_of(named)
    if plan is None:
        return PlanRuns(run_id, (_plan_run(run_id, named),), ())
    runs: list[PlanRun] = []
    undone: list[str] = []
    for other in list_run_ids(journal_dir):
        entries = read_journal(journal_file(journal_dir, other))
        if run_phase(entries) is not Phase.SORT or plan_of(entries) != plan:
            continue
        if _left_to_undo(entries):
            runs.append(_plan_run(other, entries))
        else:
            undone.append(other)
    if not runs:  # all undone already: the named run alone, as for a clean run
        return PlanRuns(run_id, (_plan_run(run_id, named),), ())
    return PlanRuns(run_id, tuple(runs), tuple(undone))


def _left_to_undo(entries: list[JournalEntry]) -> bool:
    """Tell whether a run still holds an action `undo` has not reversed.

    Args:
        entries: The run's journal.

    Returns:
        True while one action is not undone (skipped ones included).
    """
    restored = {entry.seq for entry in done_states(entries, Phase.UNDO)}
    return any(seq not in restored for seq in latest_states(entries, Phase.SORT))


def _plan_run(run_id: str, entries: list[JournalEntry]) -> PlanRun:
    """Describe a run for the list shown before undoing.

    Args:
        run_id: The run.
        entries: Its journal (not empty: a sort run moved or created something).

    Returns:
        Its start and the files it moved.
    """
    sorted_ = done_states(entries, Phase.SORT)
    moved = sum(1 for entry in sorted_ if entry.action is ActionKind.MOVE)
    return PlanRun(run_id, entries[0].at, moved)
