"""Edits kept by a narrowed run come back; the newer workbook wins over them."""

from __future__ import annotations

from media_hygiene.classify.carry_deferred import with_deferred
from media_hygiene.classify.carry_models import EditSheet, LostWhy
from media_hygiene.classify.carry_types import CarrySource
from media_hygiene.classify.models import Band, SortReason
from media_hygiene.classify.names import lost_line
from media_hygiene.classify.plan_deferred import DeferredEdits
from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow
from media_hygiene.classify.workbook.edits import Edits, Stay
from media_hygiene.classify.workbook.salvage_models import Notes, Salvaged


def row(row_id: str) -> PlanRow:
    """A row of the plan, nothing proposed."""
    return PlanRow(
        id=row_id,
        path=f"C:\\Photos\\{row_id}.jpg",
        size=1,
        mtime_ns=1,
        sha256=None,
        date=None,
        date_source=None,
        event_id="",
        values=None,
        band=Band.UNDATED,
        reason=SortReason.CALENDAR,
        score=0,
        root="C:\\Photos",
        folder=None,
        name=f"{row_id}.jpg",
    )


def source(workbook: Edits, kept: DeferredEdits | None) -> CarrySource:
    """A previous workbook and its plan, holding edits kept for later."""
    plan = ClassifyPlan(
        plan_id="p",
        layout="",
        unsure_layout="",
        rows=(row("a"),),
        events=(),
        deferred=kept,
    )
    return CarrySource("w.xlsx", "2026-10-14T10:00", Salvaged("p", workbook), plan)


def test_kept_edits_come_back_and_the_workbook_wins() -> None:
    """A kept row joins the plan; a kept edit typed again otherwise is replaced."""
    kept = DeferredEdits.of(
        ((row("b"), row("c")), ()),
        (Edits(files={"b": "2016/Kept", "c": Stay.STAY}), Notes({"b": "note"})),
    )
    merged = with_deferred(source(Edits(files={"b": "2016/Newer"}), kept))
    assert merged.plan is not None
    assert [item.id for item in merged.plan.rows] == ["a", "b", "c"]
    assert merged.plan.deferred is None
    assert merged.salvaged.edits.files == {"b": "2016/Newer", "c": Stay.STAY}
    assert merged.salvaged.notes.files == {"b": "note"}
    [replaced] = merged.salvaged.invalid
    assert (replaced.sheet, replaced.why) == (EditSheet.FILES, LostWhy.REPLACED)
    assert replaced.key.endswith("b.jpg")
    assert replaced.value == "2016/Kept"
    assert "kept by a run with --year or --path" in lost_line(replaced)


def test_nothing_kept_nothing_changed() -> None:
    """Without kept edits, the source is the same."""
    plain = source(Edits(files={"a": "X"}), None)
    assert with_deferred(plain) is plain
