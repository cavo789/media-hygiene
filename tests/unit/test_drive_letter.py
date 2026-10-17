"""A run whose drive came back under another letter: its journal paths moved (0186)."""

from __future__ import annotations

import shutil
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import ActionKind
from media_hygiene.paths.quarantines import Quarantines
from media_hygiene.services.drive_letter import LetterChange, moved_to
from media_hygiene.services.letter_refusals import COMES_BACK, refused
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from media_hygiene.actions.journal import JournalEntry

_CHANGE = LetterChange("e", "f", Path("/quarantine"), Path("/data"))


def test_paths_of_the_old_letter_move_to_the_new_one() -> None:
    """Data and quarantine of `e` under `f`; the run's inner mirror is left as it is."""
    assert _CHANGE.move("/data/e/Photos/a.jpg") == "/data/f/Photos/a.jpg"
    assert (
        _CHANGE.move("/quarantine/e/20261016-120000/e/Photos/a.jpg")
        == "/quarantine/f/20261016-120000/e/Photos/a.jpg"
    )


def test_other_paths_are_left_alone() -> None:
    """Another drive, the default quarantine, a letter that only starts a name: kept."""
    for path in ("/data/c/a.jpg", "/quarantine/2026/e/a.jpg", "/data/ex/a.jpg"):
        assert _CHANGE.move(path) == path
    assert _CHANGE.move(None) is None


def test_a_drive_holding_only_its_own_files_of_the_run_is_no_match(
    tmp_path: Path,
) -> None:
    """E: away, the run also set F:'s files aside on F:: F: is not E: renamed."""
    own = tmp_path / "quarantine" / "f"
    (own / "20261016-120000" / "f").mkdir(parents=True)
    quarantines = Quarantines(tmp_path / "quarantine", (("F:", own),))
    assert moved_to(quarantines, "20261016-120000", "E:") is None
    (own / "20261016-120000" / "e").mkdir()
    assert moved_to(quarantines, "20261016-120000", "E:") == "f"


def test_a_move_of_sort_is_never_refused_for_its_folder() -> None:
    """Only a file back from the quarantine needs its folder under the new letter."""
    assert ActionKind.MOVE not in COMES_BACK
    assert ActionKind.QUARANTINE in COMES_BACK
    assert ActionKind.DELETE_DUPLICATE in COMES_BACK


def _line(seq: int, action: ActionKind, path: Path) -> JournalEntry:
    """A done journal line."""
    return done_line(action, str(path), seq=seq)


def test_a_folder_the_run_removed_comes_back_when_its_parent_is_there(
    tmp_path: Path,
) -> None:
    """0202: Trip removed by the clean, Photos still on F:: both come back."""
    trip = tmp_path / "data" / "f" / "Photos" / "Trip"
    trip.parent.mkdir(parents=True)
    moved = [
        _line(1, ActionKind.QUARANTINE_DUPLICATE, trip / "a.jpg"),
        _line(2, ActionKind.REMOVE_FOLDER, trip),
    ]
    before = [
        entry.model_copy(update={"path": entry.path.replace("/f/", "/e/")})
        for entry in moved
    ]
    assert refused(moved, before) == {}
    shutil.rmtree(trip.parent)  # Photos deleted by hand: nothing rebuilt by guess
    assert refused(moved, before) == {1: trip / "a.jpg", 2: trip}
