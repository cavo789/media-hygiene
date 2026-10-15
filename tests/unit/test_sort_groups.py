"""Names given to the groups under way, before their files move (0163)."""

from __future__ import annotations

import random
from typing import TYPE_CHECKING

from media_hygiene.actions.sort_groups import NameBook
from media_hygiene.actions.sort_names import SourceSidecars, owners
from media_hygiene.actions.sort_plan import Move, MoveGroup
from media_hygiene.classify.models import Band
from media_hygiene.scan.sidecars import is_sidecar

if TYPE_CHECKING:
    from pathlib import Path


def group(tmp_path: Path, source: str, name: str = "IMG_1.jpg") -> MoveGroup:
    """One file of `source`, going to `tmp_path / "t"`."""
    path = tmp_path / source / name
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(source.encode())
    move = Move(name, path, len(source), 0, Band.SURE)
    return MoveGroup(tmp_path, tmp_path / "t", (move,))


def test_a_name_given_is_taken_until_handed_back(tmp_path: Path) -> None:
    """Free on the disk but given to a group under way: the next one gets ` (2)`."""
    book = NameBook()
    first = book.ready(group(tmp_path, "a"))
    second = book.ready(group(tmp_path, "b", "img_1.JPG"))  # NTFS ignores case
    assert first.targets == {"IMG_1.jpg": "IMG_1.jpg"}
    assert second.targets == {"img_1.JPG": "img_1 (2).JPG"}
    book.release(first)  # its move failed: nothing holds the name on the disk
    assert book.ready(group(tmp_path, "c")).targets == {"IMG_1.jpg": "IMG_1.jpg"}


def test_a_folder_handed_back_whole_is_forgotten(tmp_path: Path) -> None:
    """Every group of a folder ended: the name is free again, nothing is kept."""
    book = NameBook()
    ready = book.ready(group(tmp_path, "a"))
    assert ready.names == ["IMG_1.jpg"]
    book.release(ready)
    book.release(ready)  # twice: no error
    assert book.ready(group(tmp_path, "b")).targets == {"IMG_1.jpg": "IMG_1.jpg"}


def _listed_each_time(group: MoveGroup) -> list[Path]:
    """The sidecars of a group as found before 0171: the folder listed per group.

    Args:
        group: Files that move together, all in one folder.

    Returns:
        The sidecars belonging to one of them, by name.
    """
    folder = group.moves[0].source.parent
    names = [move.source.name for move in group.moves]
    found = [path for path in folder.iterdir() if path.is_file()]
    return sorted(
        path for path in found if is_sidecar(path.name) and owners(path.name, names)
    )


def _write(folder: Path, names: list[str]) -> None:
    """Create empty files.

    Args:
        folder: Where.
        names: Their names.
    """
    folder.mkdir(parents=True, exist_ok=True)
    for name in names:
        (folder / name).write_bytes(b"")


def test_a_folder_listed_once_finds_what_a_listing_per_group_found(
    tmp_path: Path,
) -> None:
    """Random folders: each group gets the same sidecars as before (0171)."""
    rnd = random.Random(171)  # noqa: S311 - test file names, not secrets
    for round_ in range(30):
        folder = tmp_path / f"r{round_}"
        stems = [f"IMG_{index}" for index in range(rnd.randint(1, 12))]
        photos = [f"{stem}.{rnd.choice(['jpg', 'JPG', 'cr2'])}" for stem in stems]
        sidecars = [
            rnd.choice([f"{stem}.xmp", f"{stem.lower()}.XMP", f"{photo}.xmp"])
            for stem, photo in zip(stems, photos, strict=True)
            if rnd.random() < 0.7
        ]
        _write(folder, [*photos, *sidecars, "notes.txt", "other.xmp"])
        (folder / "sub.xmp").mkdir()  # a folder, never a sidecar
        groups = [
            MoveGroup(
                tmp_path, tmp_path / "t", (Move(name, folder / name, 0, 0, Band.SURE),)
            )
            for name in photos
        ]
        expected = [_listed_each_time(each) for each in groups]
        found = SourceSidecars()
        assert [found.take(each) for each in groups] == expected


def test_a_sidecar_owned_by_two_groups_goes_with_the_first(tmp_path: Path) -> None:
    """`IMG_1.xmp` belongs to `IMG_1.jpg` and `IMG_1.cr2`: it moves once."""
    folder = tmp_path / "a"
    _write(folder, ["IMG_1.jpg", "IMG_1.cr2", "IMG_1.xmp", "IMG_1.cr2.xmp"])
    found = SourceSidecars()
    jpg, cr2 = (
        MoveGroup(
            tmp_path, tmp_path / "t", (Move(name, folder / name, 0, 0, Band.SURE),)
        )
        for name in ("IMG_1.jpg", "IMG_1.cr2")
    )
    assert found.take(jpg) == [folder / "IMG_1.xmp"]
    assert found.take(cr2) == [folder / "IMG_1.cr2.xmp"]


def test_a_missing_folder_has_no_sidecars(tmp_path: Path) -> None:
    """Gone since the plan: nothing to hand out, no error."""
    found = SourceSidecars()
    gone = Move("x", tmp_path / "gone" / "IMG_1.jpg", 0, 0, Band.SURE)
    assert found.take(MoveGroup(tmp_path, tmp_path / "t", (gone,))) == []
