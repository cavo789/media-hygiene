"""Names given to the groups under way, before their files move (0163)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.sort_groups import NameBook
from media_hygiene.actions.sort_plan import Move, MoveGroup
from media_hygiene.classify.models import Band

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
