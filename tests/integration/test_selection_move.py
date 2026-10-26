"""*Move to an event…* (0403): photos shown by source folder, then moved, no rule."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime, timedelta
from typing import TYPE_CHECKING

from media_hygiene.classify.folders import FolderRules
from media_hygiene.classify.own_events import named_event, one_moment
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.services.selection_models import Picked, event_path
from media_hygiene.services.selection_move import SelectionMover
from tests.support.scenes import Shot, write_shot
from tests.support.sorting import (
    PARTY,
    WEDDING,
    audited_library,
    classify,
    snapshot,
    undo,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_GAP = 18.0


def test_one_moment_is_told_by_the_gaps_between_the_dates() -> None:
    """An evening is one moment; prints of three months are not; no date is none."""
    evening = [datetime(2009, 11, 28, 18) + timedelta(hours=h) for h in range(4)]
    prints = [datetime(2009, 11, 28), datetime(2009, 12, 24), datetime(2010, 1, 3)]
    assert one_moment(evening, _GAP)
    assert not one_moment(prints, _GAP)
    assert not one_moment([], _GAP)


def test_a_named_event_is_a_meaning_of_one_moment_not_a_person() -> None:
    """`Saint Nicolas 2009` of one evening; a generic or a person's folder is not."""
    rules = FolderRules.build((), ((), ())).with_people(("Chloé",))
    evening = ([datetime(2009, 12, 5, 18), datetime(2009, 12, 5, 21)], _GAP)
    assert named_event("Saint Nicolas 2009", rules, evening)
    assert not named_event(None, rules, evening)
    assert not named_event("Photos Chloé", rules, evening)


def _ready(locations: Locations) -> tuple[Runtime, dict[int, Path]]:
    """The library of `sorting`, audited and classified; its photos by a key."""
    runtime = audited_library(locations)
    classify(runtime)
    photos = sorted((locations.data_dir / PARTY).glob("*.jpg"))
    photos += sorted((locations.data_dir / WEDDING).glob("*.jpg"))
    return runtime, dict(enumerate(photos))


def test_the_view_unticks_a_folder_named_after_another_event(
    locations: Locations,
) -> None:
    """`Mariage` (one day, a name) unticked for `Kermesse`; the dated folder ticked."""
    runtime, picked = _ready(locations)
    mover = SelectionMover(runtime)
    view = mover.view(Picked(picked), "Kermesse")
    sources = {s.folder.rsplit("\\", 1)[-1]: s for s in view.sources}
    assert sources["Juillet 2016"].ticked
    assert not sources["Mariage"].ticked
    assert sources["Mariage"].named == "Mariage"
    assert view.proposed == "Mariage"  # the user's named folder holding most of them
    assert view.target.endswith("2016\\2016-07\\Kermesse")  # the earliest's month
    assert view.month == "2016/2016-07"  # its event folders are the ones offered
    assert all(s.ticked for s in mover.view(Picked(picked), "Mariage").sources)


def test_the_move_goes_to_year_month_name_and_undo_puts_it_back(
    locations: Locations,
) -> None:
    """The party's photos to `2016/2016-07/Kermesse`, journaled; no rule written."""
    runtime, picked = _ready(locations)
    before = snapshot(locations.data_dir)
    rules = read_rules(locations.config_file)
    party = {key: path for key, path in picked.items() if PARTY in str(path)}
    done = SelectionMover(runtime).move(Picked(party), "Kermesse")
    assert done["moved"] == len(party), done
    assert done["intact"]
    moved_to = locations.data_dir / "c/2016/2016-07/Kermesse"  # the drive is the root
    assert len(list(moved_to.glob("*.jpg"))) == len(party)
    assert read_rules(locations.config_file) == rules
    undo(runtime, str(done["run_id"]))
    after = snapshot(locations.data_dir)
    assert {p: f for p, f in after.items() if p.endswith(".jpg")} == {
        p: f for p, f in before.items() if p.endswith(".jpg")
    }


def test_an_event_name_may_hold_sub_folders(locations: Locations) -> None:
    r"""`France\Morzine` goes to `2016/2016-07/France/Morzine`; empty parts dropped."""
    runtime, picked = _ready(locations)
    party = {key: path for key, path in picked.items() if PARTY in str(path)}
    mover = SelectionMover(runtime)
    assert mover.view(Picked(party), "France\\Morzine").target.endswith(
        "2016\\2016-07\\France\\Morzine"
    )
    done = mover.move(Picked(party), " France\\\\Morzine/ ")
    assert done["moved"] == len(party), done
    moved_to = locations.data_dir / "c/2016/2016-07/France/Morzine"
    assert len(list(moved_to.glob("*.jpg"))) == len(party)


def test_the_event_path_makes_each_folder_safe() -> None:
    """Each folder is made safe for Windows; the separators are kept between them."""
    assert event_path("France/Mor:zine") == "France/Mor_zine"
    assert event_path(" / ") == ""


def test_a_photo_the_plan_lacks_takes_its_month_from_the_index(
    locations: Locations,
) -> None:
    """Not in the classify plan, dated in the index: its month, not *no date*."""
    runtime, picked = _ready(locations)
    lost = {
        path.with_name("not-planned.jpg"): datetime(2009, 9, 1, 10)
        for path in picked.values()
    }
    view = SelectionMover(runtime).view(Picked(dict(enumerate(lost)), lost), "School")
    assert view.month == "2009/2009-09"


def test_a_photo_the_plan_leaves_moves_when_picked(locations: Locations) -> None:
    """Looked at (in its own month folder), the plan leaves it; picked, it moves."""
    seen = locations.data_dir / "c/2019/2019-03/IMG_9100.jpg"
    write_shot(seen, Shot(60, taken_at="2019:03:02 10:00:00"))
    runtime = audited_library(locations)
    classify(runtime)
    done = SelectionMover(runtime).move(Picked({0: seen}), "Danse")
    assert done["moved"] == 1, done
    assert (locations.data_dir / "c/2019/2019-03/Danse/IMG_9100.jpg").is_file()
