"""The review page's choices over the workbook's edits, and their file."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest
from pydantic import ValidationError

from media_hygiene.classify.carry_models import EditSheet
from media_hygiene.classify.page_decisions import (
    EventDecision,
    FileDecision,
    PageDecisions,
    read_page_decisions,
    write_page_decisions,
)
from media_hygiene.classify.page_overlay import overlay, page_cell
from media_hygiene.classify.page_values import EventValue, FileValue
from media_hygiene.classify.workbook.edits import Edits, EventEdit, Stay
from media_hygiene.errors import DecisionsError

if TYPE_CHECKING:
    from pathlib import Path

PLAN = "plan-1"
ITALY = EventValue(name="Italy")


def _page(*items: EventDecision | FileDecision) -> PageDecisions:
    """Decisions of the page for `PLAN`."""
    events = tuple(item for item in items if isinstance(item, EventDecision))
    files = tuple(item for item in items if isinstance(item, FileDecision))
    return PageDecisions(plan_id=PLAN, events=events, files=files)


def test_the_page_wins_agrees_or_conflicts() -> None:
    """Newer than the workbook it saw; the same; or the workbook changed since."""
    workbook = Edits(
        files={"r2": "2020/Old", "r3": "2020/Since"},
        events={"e2": EventEdit("Rome"), "e3": EventEdit("Italy")},
        file_cells={"r2": "Files!K2", "r3": "Files!K3"},
    )
    page = _page(
        EventDecision(event="e1", value=ITALY),
        EventDecision(event="e2", value=ITALY, base=EventValue(name="Rome")),
        EventDecision(event="e3", value=ITALY),
        EventDecision(event="e4", value=EventValue(stay=True), base=ITALY),
        FileDecision(row="r1", value=FileValue(stay=True)),
        FileDecision(
            row="r2",
            value=FileValue(folder="2020/New"),
            base=FileValue(folder="2020/Old"),
        ),
        FileDecision(row="r3", value=FileValue(folder="2020/Page")),
    )
    result = overlay(workbook, page)
    edits = result.edits
    assert (result.applied, result.replaced, result.agreed) == (4, 2, 1)
    assert edits.events["e1"] == EventEdit("Italy", "")
    assert edits.events["e2"] == EventEdit("Italy", "")
    assert "e4" not in edits.events
    assert edits.files == {"r1": Stay.STAY, "r2": "2020/New", "r3": "2020/Since"}
    assert edits.file_cells["r2"] == page_cell()
    assert edits.file_cells["r3"] == "Files!K3"
    conflicts = [
        (item.sheet, item.key, item.page, item.workbook) for item in result.conflicts
    ]
    assert conflicts == [
        (EditSheet.EVENTS, "e4", "(stay where it is)", ""),
        (EditSheet.FILES, "r3", "2020/Page", "2020/Since"),
    ]


def test_values_are_checked() -> None:
    """A folder climbing out, an empty choice, an event chosen twice are refused."""
    with pytest.raises(ValidationError, match="not a folder below the target"):
        EventValue(category="a/../b")
    with pytest.raises(ValidationError, match="without any value"):
        _page(FileDecision(row="r1", value=FileValue()))
    with pytest.raises(ValidationError, match="decided twice"):
        _page(
            EventDecision(event="e1", value=ITALY),
            EventDecision(event="e1", value=ITALY),
        )
    assert EventValue(name="Italy", category="Trips").edit() == EventEdit(
        "Italy", "Trips"
    )
    assert EventValue.of(EventEdit("", Stay.STAY)) == EventValue(stay=True)


def test_the_file_round_trip_and_its_refusals(tmp_path: Path) -> None:
    """Missing: no choice; written then read; another plan or garbage is refused."""
    path = tmp_path / "sort-decisions.json"
    assert read_page_decisions(path, PLAN) == PageDecisions(plan_id=PLAN)
    page = _page(EventDecision(event="e1", value=ITALY))
    write_page_decisions(path, page)
    assert read_page_decisions(path, PLAN) == page
    assert not list(tmp_path.glob(".*partial"))
    with pytest.raises(DecisionsError, match="another classify run"):
        read_page_decisions(path, "plan-2")
    path.write_text("{not json", encoding="utf-8")
    with pytest.raises(DecisionsError, match="not a valid decisions file") as refused:
        read_page_decisions(path, PLAN)
    assert "delete it" in (refused.value.tip or "")
