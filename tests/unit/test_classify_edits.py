"""Applying the edits: file > event > category; protected files never move."""

from __future__ import annotations

from media_hygiene.classify.models import Band, DateSource, SortReason
from media_hygiene.classify.plan_file import ClassifyPlan, PlanRow, RowValues
from media_hygiene.classify.workbook.edits import (
    CategoryEdit,
    Edits,
    EventEdit,
    Source,
    Stay,
    resolve,
)


def row(name: str, band: Band, tags: tuple[str, str] = ("", "")) -> PlanRow:
    """A row of 2016, in the band given; tags: its category and its event."""
    category, event = tags
    folders = {
        Band.SURE: f"2016/{category}",
        Band.UNSURE: f"2016/To check/{category}",
        Band.MANUAL: "2016/To sort/2016-07-14",
        Band.STAY: None,
    }
    return PlanRow(
        id=name,
        path=f"C:\\Photos\\DCIM\\{name}.jpg",
        size=1,
        mtime_ns=0,
        sha256=None,
        date="2016-07-14T10:00:00",
        date_source=DateSource.EXIF,
        event_id=event,
        values=RowValues(
            year=2016,
            month=7,
            day=14,
            category=category,
            event="2016-07-14",
            event_start="2016-07-14",
        ),
        band=band,
        reason=SortReason.EXISTING_FOLDER,
        score=90,
        root="C:\\Photos",
        folder=folders[band],
        name=f"{name}.jpg",
    )


PLAN = ClassifyPlan(
    plan_id="p",
    layout="{year}/{category}",
    unsure_layout="{year}/To check/{category}",
    rows=(
        row("sure", Band.SURE, ("Mer", "")),
        row("check", Band.UNSURE, ("Mer", "")),
        row("loose", Band.MANUAL, ("", "e1")),
        row("kept", Band.STAY, ("Mer", "e1")),
    ),
    events=(),
)


def folders(edits: Edits) -> dict[str, str | None]:
    """The folder of every row once the edits are applied."""
    return {d.row.id: d.folder for d in resolve(PLAN, edits)}


def test_a_renamed_category_moves_its_sure_and_to_check_files() -> None:
    """The "to check" files keep their band until confirmed."""
    renamed = folders(Edits(categories={"Mer": CategoryEdit("Vacances/Mer")}))
    assert renamed["sure"] == "2016/Vacances/Mer"
    assert renamed["check"] == "2016/To check/Vacances/Mer"


def test_confirming_a_category_makes_its_to_check_files_sure() -> None:
    """One cell confirms the whole category."""
    decisions = resolve(PLAN, Edits(categories={"Mer": CategoryEdit(confirm=True)}))
    check = next(d for d in decisions if d.row.id == "check")
    assert (check.folder, check.band) == ("2016/Mer", Band.SURE)


def test_an_event_name_is_its_category_unless_one_is_chosen() -> None:
    """`Kermesse` names the folder; a chosen category wins; stay leaves it."""
    assert folders(Edits(events={"e1": EventEdit("Kermesse")}))["loose"] == (
        "2016/Kermesse"
    )
    chosen = Edits(events={"e1": EventEdit("Kermesse", "École")})
    assert folders(chosen)["loose"] == "2016/École"
    stay = Edits(events={"e1": EventEdit(category=Stay.STAY)})
    assert folders(stay)["loose"] is None


def test_a_file_edit_wins_over_its_category() -> None:
    """File > category, and "stay" at category level leaves the files."""
    edits = Edits(
        files={"sure": "2016/Plage"},
        categories={"Mer": CategoryEdit(Stay.STAY)},
    )
    found = folders(edits)
    assert found["sure"] == "2016/Plage"
    assert found["check"] is None
    sources = {d.row.id: d.source for d in resolve(PLAN, edits)}
    assert sources == {
        "sure": Source.FILE,
        "check": Source.GROUP,
        "loose": Source.PROPOSAL,
        "kept": Source.PROPOSAL,
    }


def test_protected_files_ignore_every_edit() -> None:
    """A file left as it is never moves, whatever the workbook says."""
    edits = Edits(
        files={"kept": "2016/Ailleurs"},
        events={"e1": EventEdit("Kermesse")},
        categories={"Mer": CategoryEdit("Autre")},
    )
    assert folders(edits)["kept"] is None
