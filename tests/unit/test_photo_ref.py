"""One photo reference, `{path, id}` (TODO 0551): one test per move event.

The tool's own moves (`sort`, `undo`, the quarantine and back) follow the paths at once;
a rename in Explorer is found again by id at the next audit; a copy on another drive,
an edited copy and two identical copies each have their answer.
"""

from __future__ import annotations

import tomllib
from typing import TYPE_CHECKING, Final

from media_hygiene.config.photo_ref import (
    PhotoRef,
    content_id,
    follow_paths,
    ref_line,
    relocate,
    size_of,
    write_refs,
)
from media_hygiene.config.place_photos import PlacePhotos
from media_hygiene.places.config_photos import give_photos, read_place_photos
from media_hygiene.places.photo_moves import (
    follow_place_photos,
    ids_wanted,
    relocate_place_photos,
)

if TYPE_CHECKING:
    from pathlib import Path

OLD: Final = "C:\\Photos\\2024\\IMG_0096.JPG"
ID: Final = content_id("fc7749d8b88880b3" + "0" * 48, 2484373)
REF: Final = PhotoRef(path=OLD, id=ID)


def test_the_id_is_sixteen_hex_and_the_size() -> None:
    """The form of the TODO; its size read back."""
    assert ID == "fc7749d8b88880b3:2484373"
    assert size_of(ID) == 2484373


def test_the_form_before_0551_is_read() -> None:
    """`sha256` + `size`: an id."""
    old = PhotoRef.model_validate({"sha256": "ab" * 32, "size": 5, "path": OLD})
    assert old == PhotoRef(path=OLD, id="abababababababab:5")


def test_sort_then_undo_follow_the_path() -> None:
    """Sorted: the new path; undone: home again."""
    sorted_to = "C:\\Photos\\Events\\Geer\\IMG_0096.JPG"
    moved = follow_paths([REF], {OLD: sorted_to})
    assert moved[0].path == sorted_to
    assert follow_paths(moved, {sorted_to: OLD}) == [REF]


def test_quarantine_and_back_never_loops() -> None:
    """A → quarantine → A in the same moves: the path stays itself."""
    aside = "C:\\media-hygiene\\quarantine\\IMG_0096.JPG"
    assert follow_paths([REF], {OLD: aside, aside: OLD}) == [REF]
    assert follow_paths([REF], {OLD: aside})[0].path == aside


def test_an_explorer_rename_is_found_by_id() -> None:
    """The old path gone, the id found elsewhere: the path is rewritten."""
    renamed = "C:\\Photos\\2024 Geer\\IMG_0096.JPG"
    assert relocate([REF], {ID: [renamed]})[0].path == renamed


def test_a_copy_on_another_drive_changes_nothing() -> None:
    """The path still holds the id: it stays."""
    assert relocate([REF], {ID: ["D:\\Backup\\IMG_0096.JPG", OLD]}) == [REF]


def test_an_edited_copy_is_another_photo() -> None:
    """A new content, a new id: the reference keeps its path, found nowhere."""
    assert relocate([REF], {content_id("1" * 64, 2484380): [OLD]}) == [REF]


def test_two_identical_copies_the_same_name_wins_then_the_path() -> None:
    """The same answer on every run."""
    copies = ["C:\\A\\copy.jpg", "C:\\B\\IMG_0096.JPG", "C:\\C\\IMG_0096.JPG"]
    assert relocate([REF], {ID: copies[::-1]})[0].path == copies[1]
    other = PhotoRef(path="C:\\gone\\x.jpg", id=ID)
    assert relocate([other], {ID: copies[::-1]})[0].path == copies[0]


def test_written_lines_read_back(tmp_path: Path) -> None:
    """Literal Windows paths, a quote escaped, an extra key."""
    odd = PhotoRef(path="C:\\l'été\\a.jpg", id=ID)
    file = tmp_path / "x" / "refs.toml"
    write_refs(file, "header", {"faces": [ref_line(REF, {"face": 2}), ref_line(odd)]})
    faces = tomllib.loads(file.read_text("utf-8"))["faces"]
    assert faces == [{"path": OLD, "id": ID, "face": 2}, {"path": odd.path, "id": ID}]


def test_places_follow_moves_and_renames(tmp_path: Path) -> None:
    """Saved, followed, relocated: each read back from the disk, counted."""
    config = tmp_path / "config.toml"
    assert follow_place_photos(config, {OLD: "x"}) == 0
    config.write_text("# mine\n", "utf-8")
    give_photos(config, PlacePhotos(place="Geer", photos=(REF,)))
    assert ids_wanted(config) == {ID}
    sorted_to = "C:\\Photos\\Events\\IMG_0096.JPG"
    assert follow_place_photos(config, {OLD: sorted_to}) == 1
    assert follow_place_photos(config, {OLD: sorted_to}) == 0
    assert relocate_place_photos(config, {ID: [OLD]}) == 1
    assert read_place_photos(config)[0].photos == (REF,)
    assert config.read_text("utf-8").startswith("# mine\n")
