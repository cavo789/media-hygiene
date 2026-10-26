"""Applying the edits: file > event > category; protected files never move."""

from __future__ import annotations

from media_hygiene.classify.models import Band, SortReason
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
        row("kept", Band.STAY, ("Mer", "e1")).model_copy(
            update={"reason": SortReason.LEFT_AS_IS}
        ),
        row("seen", Band.STAY, ("Mer", "e1")).model_copy(
            update={"reason": SortReason.NOTHING_SPECIAL, "values": None}
        ),
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
        "seen": Source.PROPOSAL,
    }


def test_protected_files_ignore_every_edit() -> None:
    """A file left as it is never moves, whatever the workbook says."""
    edits = Edits(
        files={"kept": "2016/Ailleurs"},
        events={"e1": EventEdit("Kermesse")},
        categories={"Mer": CategoryEdit("Autre")},
    )
    assert folders(edits)["kept"] is None


def test_a_file_the_plan_leaves_moves_by_its_own_edit_only() -> None:
    """Looked at (not protected): its file edit moves it; an event edit does not."""
    edits = Edits(files={"seen": "2016/2016-07/Danse"}, events={"e1": EventEdit("X")})
    assert folders(edits)["seen"] == "2016/2016-07/Danse"
    assert folders(Edits(events={"e1": EventEdit("X")}))["seen"] is None


# 0385: an event choice never flattens the folders the user named.
TRIP = plan_of(
    (
        row("budva", Band.SURE, ("Montenegro/Budva", "trip")),
        row("cetinje", Band.SURE, ("Montenegro/Cetinje", "trip")),
        row("chloe", Band.SURE, ("Photos Chloé", "trip")),
        row("chloe2", Band.SURE, ("Photos Chloé", "trip")),
        row("loose", Band.MANUAL, ("", "trip")),
        row("check", Band.UNSURE, ("Photos Chloé", "trip")),
        row("generic", Band.SURE, ("Photos Chloé", "trip")).model_copy(
            update={"reason": SortReason.EVENT_NEIGHBOUR}
        ),
        row("fixed", Band.STAY, ("Montenegro/Budva", "trip")),
    )
)


def trip_folders(edits: Edits) -> dict[str, str | None]:
    """The folder of every row of the trip once the edits are applied."""
    return {d.row.id: d.folder for d in resolve(TRIP, edits)}


def test_accepting_the_proposal_keeps_the_user_named_folders() -> None:
    """Enter / V on the trip: only the loose files go to the proposed folder."""
    found = trip_folders(Edits(events={"trip": EventEdit("", "Photos Chloé")}))
    assert found["budva"] == "2016/Montenegro/Budva"
    assert found["cetinje"] == "2016/Montenegro/Cetinje"
    assert found["chloe"] == "2016/Photos Chloé"
    assert found["loose"] == "2016/Photos Chloé"
    assert found["check"] == "2016/Photos Chloé"
    assert found["generic"] == "2016/Photos Chloé"
    assert found["fixed"] is None


def test_a_name_with_the_proposed_category_keeps_them_too() -> None:
    """The name is not a destination when the category is the proposed one."""
    found = trip_folders(Edits(events={"trip": EventEdit("Été", "photos chloé")}))
    assert found["budva"] == "2016/Montenegro/Budva"
    assert found["loose"] == "2016/photos chloé"


def test_a_destination_becomes_the_parent_of_the_user_named_folders() -> None:
    """Below the common parent: nothing shared with `Photos Chloé`, so all of it."""
    edits = Edits(events={"trip": EventEdit("", "Vacances")})
    found = trip_folders(edits)
    assert found["budva"] == "2016/Vacances/Montenegro/Budva"
    assert found["chloe"] == "2016/Vacances/Photos Chloé"
    assert found["loose"] == "2016/Vacances"
    assert found["generic"] == "2016/Vacances"
    bands = {d.row.id: d.band for d in resolve(TRIP, edits)}
    assert bands["budva"] is Band.SURE


def test_the_common_parent_is_left_out_under_a_destination() -> None:
    """`Montenegro/Budva`, `Montenegro/Cetinje` → `<destination>/Budva`, `…/Cetinje`."""
    plan = plan_of(
        (
            row("budva", Band.SURE, ("Montenegro/Budva", "trip")),
            row("cetinje", Band.SURE, ("Montenegro/Cetinje", "trip")),
            row("loose", Band.MANUAL, ("", "trip")),
        )
    )
    edits = Edits(events={"trip": EventEdit("", "Vacances au Monténégro")})
    found = {d.row.id: d.folder for d in resolve(plan, edits)}
    assert found == {
        "budva": "2016/Vacances au Monténégro/Budva",
        "cetinje": "2016/Vacances au Monténégro/Cetinje",
        "loose": "2016/Vacances au Monténégro",
    }


def test_a_single_user_named_folder_becomes_the_destination() -> None:
    """No `Budva/Budva`: the one folder is renamed by the event's destination."""
    plan = plan_of(
        (
            row("budva", Band.SURE, ("Montenegro/Budva", "trip")),
            row("loose", Band.MANUAL, ("", "trip")),
        )
    )
    found = {
        d.row.id: d.folder
        for d in resolve(plan, Edits(events={"trip": EventEdit("Kotor")}))
    }
    assert found == {"budva": "2016/Kotor", "loose": "2016/Kotor"}


def test_a_file_edit_still_moves_a_file_of_a_user_named_folder() -> None:
    """The user may move one such file on purpose."""
    edits = Edits(
        files={"budva": "2016/Ailleurs"},
        events={"trip": EventEdit("", "Photos Chloé")},
    )
    assert trip_folders(edits)["budva"] == "2016/Ailleurs"


def test_a_kept_user_named_folder_follows_a_category_rename() -> None:
    """Merging two named folders stays possible by renaming a category."""
    edits = Edits(
        events={"trip": EventEdit("", "Photos Chloé")},
        categories={"Montenegro/Budva": CategoryEdit("Montenegro/Kotor")},
    )
    assert trip_folders(edits)["budva"] == "2016/Montenegro/Kotor"
