"""0390: `sort --event`, *Sort this event now*: one event's files, journaled, undone."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.errors import WorkbookError
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.runtime import Runtime
from media_hygiene.services.sort_event import only_event, sort_event, sorter_of
from media_hygiene.services.sort_inputs import find_workbook, load_inputs
from media_hygiene.services.sort_reviewing import open_sort_review
from tests.support.layouts import LEGACY_LAYOUTS
from tests.support.runtime import make_runtime
from tests.support.scenes import Shot, write_shot
from tests.support.sort_review import EventsPage, app_of, call
from tests.support.sorting import PARTY, PHOTOS, build_library, classify, snapshot, undo

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

SPRING = f"{PHOTOS}/2017/Mai 2017"
SPRING_SHOTS = 5


def two_events(locations: Locations) -> tuple[Runtime, Path, dict[str, int]]:
    """The library of `sorting` and a second event, audited and classified.

    Returns:
        The runtime, the workbook, and the size of each event by id.
    """
    build_library(locations.data_dir)
    for index in range(SPRING_SHOTS):
        shot = Shot(70 + index, taken_at=f"2017:05:01 1{index}:00:00")
        write_shot(locations.data_dir / SPRING / f"P_{index:04d}.jpg", shot)
    # Events unnamed move only to a "to sort" folder: the layouts of before 0402.
    runtime = make_runtime(locations, {"classify": dict(LEGACY_LAYOUTS)})
    AuditService(runtime, NullProgress()).run()
    workbook = classify(runtime)
    plan = ClassifyPlan.model_validate_json(
        workbook.with_name("plan.json").read_text("utf-8")
    )
    sizes = {event.id: len(event.rows) for event in plan.events}
    return runtime, workbook, sizes


def test_one_event_sorted_then_the_other_two_runs_two_undos(
    locations: Locations,
) -> None:
    """Only the event's files move; each run is undone on its own."""
    runtime, workbook, sizes = two_events(locations)
    party, spring = sorted(sizes, key=lambda event: -sizes[event])
    data = locations.data_dir
    before = snapshot(data)
    first = sort_event(runtime, str(workbook), party)
    assert first is not None
    assert first.manifest.intact
    assert first.manifest.moved == sizes[party]
    assert not list((data / PARTY).glob("*.jpg"))
    assert len(list((data / SPRING).glob("*.jpg"))) == SPRING_SHOTS
    second = sort_event(runtime, str(workbook), spring)
    assert second is not None
    assert second.manifest.moved == SPRING_SHOTS
    assert sort_event(runtime, str(workbook), party) is None  # nothing left to move
    undo(runtime, second.run_id)
    assert len(list((data / SPRING).glob("*.jpg"))) == SPRING_SHOTS
    assert not list((data / PARTY).glob("*.jpg"))
    undo(runtime, first.run_id)
    after = snapshot(data)
    moved_back = {path: facts for path, facts in after.items() if path.endswith(".jpg")}
    assert moved_back == {p: f for p, f in before.items() if p.endswith(".jpg")}


def test_an_unknown_event_is_said(locations: Locations) -> None:
    """`--event` with an id the plan does not hold: a sentence, nothing moves."""
    runtime, workbook, _sizes = two_events(locations)
    inputs = load_inputs(runtime, find_workbook(runtime, str(workbook)))
    with pytest.raises(WorkbookError, match="no event"):
        only_event(inputs, "nope")


def page_of(runtime: Runtime) -> EventsPage:
    """The Events view of the latest classify run, able to sort."""
    session = open_sort_review(runtime, None)
    return app_of(session, sorter_of(runtime, session))


def test_the_page_sorts_one_event_and_shows_it_sorted(locations: Locations) -> None:
    """The run read back; the event sorted, skipped as open."""
    runtime, _workbook, sizes = two_events(locations)
    party = max(sizes, key=lambda event: sizes[event])
    app = page_of(runtime)

    done = asyncio.run(call(app, "POST /api/sort-now", {"event": party}))
    answer = json.loads(done.body)
    assert answer["moved"] == answer["verified"] == sizes[party]
    assert answer["intact"]
    assert answer["view"]["card"]["sorted"]


def test_the_page_says_what_is_missing_instead_of_moving(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No persistent journal: refused with the sentence, nothing moves."""
    runtime, _workbook, sizes = two_events(locations)
    party = max(sizes, key=lambda event: sizes[event])
    app = page_of(runtime)
    before = snapshot(locations.data_dir)
    monkeypatch.setattr(Runtime, "persistent", lambda _self, _kind: False)
    answer = asyncio.run(call(app, "POST /api/sort-now", {"event": party}))
    assert answer.status is HTTPStatus.CONFLICT
    assert "journal" in json.loads(answer.body)["error"]
    assert snapshot(locations.data_dir) == before


def test_a_page_without_a_sorter_refuses(locations: Locations) -> None:
    """Opened without the means to move: the route says to use the terminal."""
    runtime, _workbook, sizes = two_events(locations)
    app = app_of(open_sort_review(runtime, None))
    answer = asyncio.run(call(app, "POST /api/sort-now", {"event": next(iter(sizes))}))
    assert answer.status is HTTPStatus.CONFLICT
    assert "sort --event" in json.loads(answer.body)["error"]
