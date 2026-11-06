"""*Move to their month* (0623): each photo to its own month, no event folder."""

# classify works on naive local dates, as EXIF writes them.
# ruff: noqa: DTZ001

from __future__ import annotations

from datetime import datetime
from typing import TYPE_CHECKING

import pytest

from media_hygiene.classify.convention import place_of_path
from media_hygiene.services.group_match import sits_in
from media_hygiene.services.month_move import month_view, move_to_months
from media_hygiene.services.selection_models import Picked
from media_hygiene.services.selection_move import SelectionMover
from tests.support.scenes import Shot, write_shot
from tests.support.sorting import (
    PARTY,
    PARTY_SHOTS,
    WEDDING,
    audited_library,
    classify,
    snapshot,
    undo,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

_JULY = "c/2016/2016-07"  # the drive is the root of the library
_JUNE = "c/2018/2018-06"
_SIDECARS = 1  # the wedding's `.xmp` moves with its photo, counted by the run


def _ready(locations: Locations) -> tuple[SelectionMover, dict[int, Path]]:
    """The library classified; its party and wedding photos, two months, by a key."""
    runtime = audited_library(locations)
    classify(runtime)
    photos = sorted((locations.data_dir / PARTY).glob("*.jpg"))
    photos += sorted((locations.data_dir / WEDDING).glob("*.jpg"))
    return SelectionMover(runtime), dict(enumerate(photos))


def _jpegs(locations: Locations) -> dict[str, tuple[str, int]]:
    """The pictures of the library, as the disk holds them."""
    found = snapshot(locations.data_dir)
    return {path: held for path, held in found.items() if path.endswith(".jpg")}


def test_photos_of_two_months_end_in_their_months_and_undo_puts_them_back(
    locations: Locations,
) -> None:
    """No event folder, each in its own month, sorted; undo restores every file."""
    mover, picked = _ready(locations)
    before = _jpegs(locations)
    view = month_view(mover, Picked(picked))
    assert view.moves == len(picked)
    assert [group.target.rsplit("\\", 2)[1:] for group in view.months] == [
        ["2016", "2016-07"],
        ["2018", "2018-06"],
    ]
    done = move_to_months(mover, Picked(picked))
    assert done["moved"] == len(picked) + _SIDECARS, done
    assert done["intact"]
    july = list((locations.data_dir / _JULY).glob("*"))
    june = list((locations.data_dir / _JUNE).glob("*.jpg"))
    assert len([p for p in july if p.suffix == ".jpg"]) == PARTY_SHOTS
    assert len(june) == len(picked) - PARTY_SHOTS
    assert not [p for p in july if p.is_dir()]  # no event folder
    assert all(place_of_path(str(path)) != "left" for path in (*july, *june))
    undo(mover.runtime, str(done["run_id"]))
    assert _jpegs(locations) == before


def test_a_file_without_a_date_stays_and_is_said(locations: Locations) -> None:
    """Imported since `classify`, no date in the index: never guessed, counted."""
    mover, picked = _ready(locations)
    loose = locations.data_dir / PARTY / "scan.jpg"
    write_shot(loose, Shot(70))
    held = loose.read_bytes()
    chosen = Picked({**picked, 99: loose})
    assert month_view(mover, chosen).undated == (99,)
    done = move_to_months(mover, chosen)
    assert done["moved"] == len(picked) + _SIDECARS, done
    assert done["undated"] == 1
    assert "1 file has no date" in str(done["kept"])
    assert loose.read_bytes() == held


def test_only_nothing_to_move_makes_no_run(locations: Locations) -> None:
    """Only a file without a date: no run, no error, it stays."""
    mover, _picked = _ready(locations)
    loose = locations.data_dir / PARTY / "scan.jpg"
    write_shot(loose, Shot(70))
    done = move_to_months(mover, Picked({1: loose}))
    assert done["run_id"] == ""
    assert done["undated"] == 1
    assert loose.is_file()


@pytest.mark.parametrize(
    ("host", "root", "there"),
    [
        (r"C:\2016\2016-07\a.jpg", None, True),
        (r"C:\Photos\2016\2016-07\a.jpg", None, True),
        (r"C:\2016\2016-07\Event\a.jpg", None, False),  # in an event, not in the month
        (r"C:\x2016\2016-07\a.jpg", None, False),  # another folder's name
        (r"C:\2016\2016-07\a.jpg", "C:\\", True),
        (r"C:\Old\2016\2016-07\a.jpg", r"C:\New", False),  # below another target
        (r"C:\New\2016\2016-07\Event\a.jpg", r"C:\New", False),
    ],
)
def test_in_its_month_means_directly_there(
    host: str, root: str | None, *, there: bool
) -> None:
    """The month itself holds the file: an event of that month does not count."""
    assert sits_in(host, "2016/2016-07", root) is there


def test_a_file_in_its_month_stays_one_in_an_event_of_it_moves(
    locations: Locations,
) -> None:
    """Already there: counted, untouched. In `…/Kermesse`: to the month itself."""
    month = locations.data_dir / _JULY
    there, event = month / "there.jpg", month / "Kermesse" / "event.jpg"
    write_shot(there, Shot(71))
    write_shot(event, Shot(72))  # both known to the index and the plan
    mover, _picked = _ready(locations)
    when = datetime(2016, 7, 14)
    chosen = Picked({1: there, 2: event}, {there: when, event: when})
    view = month_view(mover, chosen)
    assert view.there == (1,)
    assert view.moves == 1
    done = move_to_months(mover, chosen)
    assert done["there"] == 1
    assert "already in its month" in str(done["kept"])
    assert there.is_file()
    assert not event.exists()
    assert (month / "event.jpg").is_file()


def test_a_target_chosen_holds_the_months(locations: Locations) -> None:
    """Below the target, undone; the month below the target only counts as there."""
    mover, picked = _ready(locations)
    before = _jpegs(locations)
    target = locations.data_dir / "c/Sorted"
    with locations.config_file.open("a", encoding="utf-8") as config:
        config.write(f"\n[classify]\ntarget = '{target}'\n")
    assert (
        month_view(mover, Picked(picked))
        .months[0]
        .target.endswith("Sorted\\2016\\2016-07")
    )
    done = move_to_months(mover, Picked(picked))
    assert done["moved"] == len(picked) + _SIDECARS, done
    assert len(list((target / "2016/2016-07").glob("*.jpg"))) == PARTY_SHOTS
    assert len(list((target / "2018/2018-06").glob("*.jpg"))) == 3
    undo(mover.runtime, str(done["run_id"]))
    assert _jpegs(locations) == before
