"""Sorting little by little (0398): what is sorted, what is in place, what is left.

Read from the plan and the journal, never from a staging folder: a row is *sorted* when
a `sort` run of the plan moved it and `undo` did not take it back; *in place* when it
stays, or already sits where the plan puts it; *left* otherwise. An event is sorted when
some of its rows moved and none is left. The runs of the plan, the latest first, each
with its events, its files and its undo line, are the page's history.
"""

from __future__ import annotations

from collections import defaultdict
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

from media_hygiene.actions.run_stamps import run_started

if TYPE_CHECKING:
    from collections.abc import Collection, Sequence

    from media_hygiene.actions.sort_resume import PlanRun
    from media_hygiene.classify.plan_file import ClassifyPlan

_FROZEN = ConfigDict(frozen=True, extra="forbid")
_SHOWN_EVENTS = 2  # names of events in a run's line, then "…"


class SortProgress(BaseModel):
    """The counts of the progress line."""

    model_config = _FROZEN

    sorted_events: int
    sorted_files: int
    in_place: int  # files that stay, or already sit where the plan puts them
    left_events: int
    left_files: int


class RunLine(BaseModel):
    """One `sort` run of the plan, for the history."""

    model_config = _FROZEN

    run_id: str
    started: str  # ISO 8601: the page shows it in local time
    events: tuple[str, ...]  # the titles of its first events
    more: int  # events not named
    files: int
    undone: bool


class ProgressView(BaseModel):
    """`GET /api/progress`: the counts and the runs, read again after each GO."""

    model_config = _FROZEN

    progress: SortProgress
    runs: tuple[RunLine, ...]


def sort_progress(plan: ClassifyPlan, moved: Collection[str]) -> SortProgress:
    """Count what is sorted, in place and left.

    Args:
        plan: The plan.
        moved: The rows `sort` runs moved and `undo` did not take back.

    Returns:
        The counts.
    """
    done: defaultdict[str, int] = defaultdict(int)
    left: defaultdict[str, int] = defaultdict(int)
    in_place = 0
    for row in plan.rows:
        if row.id in moved:
            done[row.event_id] += 1
        elif row.values is None or row.folder is None or row.in_place:
            in_place += 1
        else:
            left[row.event_id] += 1
    return SortProgress(
        sorted_events=sum(1 for event in done if event and event not in left),
        sorted_files=sum(done.values()),
        in_place=in_place,
        left_events=sum(1 for event in left if event),
        left_files=sum(left.values()),
    )


def run_lines(plan: ClassifyPlan, runs: Sequence[PlanRun]) -> tuple[RunLine, ...]:
    """Describe the runs of the plan for the history.

    Args:
        plan: The plan: the events' titles.
        runs: Its runs, the latest first.

    Returns:
        One line per run.
    """
    event_of = {row.id: row.event_id for row in plan.rows}
    titles = {event.id: event.label or event.span for event in plan.events}
    lines = []
    for run in runs:
        events = list(dict.fromkeys(event_of.get(row, "") for row in run.rows))
        named = [titles.get(event, "") for event in events if event]
        lines.append(
            RunLine(
                run_id=run.run_id,
                started=run_started(run.run_id).isoformat(),
                events=tuple(named[:_SHOWN_EVENTS]),
                more=max(len(named) - _SHOWN_EVENTS, 0),
                files=len(run.rows),
                undone=run.undone,
            )
        )
    return tuple(lines)
