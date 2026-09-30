"""A new `classify` carries the edits of the previous workbook over, by content."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.carry_models import EditSheet, LostWhy
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.classify.workbook.edits import resolve
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.services.carry import CarryRequest
from tests.support.carrying import (
    SPLIT,
    WEDDING,
    build_day,
    edit,
    event_name,
    final,
    plan_of,
    rename,
    run_classify,
)
from tests.support.runtime import make_runtime
from tests.support.sorting import sort

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def test_edits_land_on_the_new_plan_after_a_setting_changed(
    locations: Locations,
) -> None:
    """Files, events, categories carried; a split event named twice; a gone file."""
    build_day(locations.data_dir)
    runtime = make_runtime(locations)
    first = run_classify(runtime)
    workbook = first.folder / "classify.xlsx"
    edit(
        workbook,
        final("M0.jpg", "2018/Wedding day")
        | final("M1.jpg", "2018/Gone")
        | event_name(2, "Fair")
        | rename("Mariage", "Wedding"),
    )
    (locations.data_dir / WEDDING / "M1.jpg").unlink()
    second = run_classify(runtime.with_overrides(SPLIT))
    plan = plan_of(second)
    assert second.carried is not None
    assert second.carried.split == ("Fair",)
    assert [(lost.sheet, lost.why) for lost in second.carried.lost] == [
        (EditSheet.FILES, LostWhy.GONE)
    ]
    assert second.carried.lost[0].key.endswith("M1.jpg")
    assert len(plan.events) == 2
    edits = read_edits(second.folder / "classify.xlsx", plan)  # sort accepts it
    assert {e.name for e in edits.events.values()} == {"Fair"}
    assert len(edits.events) == 2
    rows = {row.name: row for row in plan.rows}
    assert rows["M0.jpg"].folder == "2018/Wedding day"
    assert rows["M0.jpg"].reason is SortReason.CARRIED_OVER
    assert rows["M2.jpg"].folder == "2018/Wedding"
    assert {rows[f"A{i}.jpg"].folder for i in range(5)} == {"2017/Fair"}
    assert all(row.band is Band.SURE for row in plan.rows)
    decided = {d.row.name: d.folder for d in resolve(plan, edits)}
    assert decided == {row.name: row.folder for row in plan.rows}


def test_two_named_events_merged_keep_the_larger_one(locations: Locations) -> None:
    """The name of the event bringing most files wins; the other one is listed."""
    build_day(locations.data_dir)
    runtime = make_runtime(locations)
    first = run_classify(runtime.with_overrides(SPLIT))
    edit(
        first.folder / "classify.xlsx",
        event_name(2, "Afternoon") | event_name(3, "Morning"),
    )
    second = run_classify(runtime)
    assert second.carried is not None
    names = {row.folder for row in plan_of(second).rows if row.event_id}
    assert names == {"2017/Afternoon"}
    lost = second.carried.lost
    assert [(item.value, item.why) for item in lost] == [("Morning", LostWhy.MERGED)]


def test_edits_a_sort_applied_are_not_carried(locations: Locations) -> None:
    """After a partial sort, only the edits of the files not moved yet are carried."""
    build_day(locations.data_dir)
    runtime = make_runtime(locations)
    first = run_classify(runtime)
    edit(
        first.folder / "classify.xlsx",
        final("M0.jpg", "2018/First") | final("A0.jpg", "2017/Second"),
    )
    calls = iter([False, True])
    result = sort(runtime, stop=lambda: next(calls, True))
    assert result.moves.interrupted
    moved = {entry.path.rsplit("/", 1)[-1] for entry in result.moves.moved}
    second = run_classify(runtime)
    assert second.carried is not None
    carried = {
        row.name for row in plan_of(second).rows if row.reason.value == "carried-over"
    }
    assert carried == {"A0.jpg", "M0.jpg"} - moved
    assert len(moved & {"A0.jpg", "M0.jpg"}) == 1


def test_nothing_is_carried_when_asked_or_when_nothing_was_typed(
    locations: Locations,
) -> None:
    """`--no-carry-over`, or an untouched workbook: no record of a carry."""
    build_day(locations.data_dir)
    runtime = make_runtime(locations)
    first = run_classify(runtime)
    assert first.carried is None
    untouched = run_classify(runtime)
    assert untouched.carried is not None
    assert not untouched.carried.edits
    edit(untouched.folder / "classify.xlsx", final("M0.jpg", "2018/Kept"))
    fresh = run_classify(runtime, CarryRequest(enabled=False))
    assert fresh.carried is None
    named = run_classify(runtime, CarryRequest(str(untouched.folder / "classify.xlsx")))
    assert named.carried is not None
    assert named.carried.edits == 1
