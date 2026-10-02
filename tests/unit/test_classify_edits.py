"""Applying the edits: file > event > category; protected files never move."""

from __future__ import annotations

from media_hygiene.classify.models import Band
from media_hygiene.classify.workbook.edits import (
    CategoryEdit,
    Edits,
    EventEdit,
    Source,
    Stay,
    resolve,
)
from tests.support.plans import plan_of, row

PLAN = plan_of(
    (
        row("sure", Band.SURE, ("Mer", "")),
        row("check", Band.UNSURE, ("Mer", "")),
        row("loose", Band.MANUAL, ("", "e1")),
        row("kept", Band.STAY, ("Mer", "e1")),
    )
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
