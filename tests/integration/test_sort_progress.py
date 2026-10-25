"""0398: sorting little by little: what is sorted, in place, left; the plan's runs."""

from __future__ import annotations

import asyncio
import json
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_resume import plan_runs
from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.services.sort_event import sort_event
from media_hygiene.services.sort_figures import sort_figures
from tests.integration.test_sort_event import page_of, two_events
from tests.support.sort_review import call
from tests.support.sorting import undo

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_two_runs_one_undone_counted_and_listed(locations: Locations) -> None:
    """The run undone counts nothing; the history lists both, the latest first."""
    runtime, workbook, sizes = two_events(locations)
    party, spring = sorted(sizes, key=lambda event: -sizes[event])
    plan_file = workbook.with_name("plan.json")
    journal = locations.journal_dir
    before = sort_figures(plan_file, journal)
    assert before is not None
    assert before.sorted_files == 0
    first = sort_event(runtime, str(workbook), party)
    second = sort_event(runtime, str(workbook), spring)
    assert first is not None
    assert second is not None
    undo(runtime, second.run_id)
    after = sort_figures(plan_file, journal)
    assert after is not None
    assert (after.sorted_events, after.sorted_files) == (1, sizes[party])
    assert after.left_files == before.left_files - sizes[party]
    assert after.in_place == before.in_place
    plan_id = ClassifyPlan.model_validate_json(plan_file.read_text("utf-8")).plan_id
    runs = plan_runs(journal, plan_id)
    assert [(run.run_id, run.undone) for run in runs] == [
        (second.run_id, True),
        (first.run_id, False),
    ]
    assert len(runs[1].rows) == sizes[party]


def test_the_page_reads_the_progress_again_after_a_go(locations: Locations) -> None:
    """`GET /api/progress`: the counts and the runs, from the journal, after a GO."""
    runtime, _workbook, sizes = two_events(locations)
    party = max(sizes, key=lambda event: sizes[event])
    app = page_of(runtime)

    async def act() -> tuple[dict[str, object], dict[str, object]]:
        before = json.loads((await call(app, "GET /api/progress")).body)
        await call(app, "POST /api/sort-now", {"event": party})
        return before, json.loads((await call(app, "GET /api/progress")).body)

    before, after = asyncio.run(act())
    assert before["runs"] == []
    progress = after["progress"]
    assert isinstance(progress, dict)
    assert progress["sorted_files"] == sizes[party]
    runs = after["runs"]
    assert isinstance(runs, list)
    (run,) = runs
    assert run["files"] == sizes[party]
    assert not run["undone"]
    assert run["events"]
