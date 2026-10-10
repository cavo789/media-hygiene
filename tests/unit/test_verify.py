"""Last-moment checks before deleting a duplicate copy."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.verify import burst_blocker, checked_removal
from media_hygiene.constants import MediaKind
from media_hygiene.scan.hashing import full_digest, identical_digest
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from pathlib import Path


def removal_blocker(keeper: Path, candidate: Path, size: int) -> str | None:
    """The reason `checked_removal` gives, if any."""
    return checked_removal(keeper, candidate, size).reason


def test_identical_files_can_be_removed(tmp_path: Path) -> None:
    """Same size, same bytes: no blocker, and the SHA-256 of the same reading."""
    keeper, copy = tmp_path / "keeper", tmp_path / "copy"
    keeper.write_bytes(b"same")
    copy.write_bytes(b"same")
    removal = checked_removal(keeper, copy, 4)
    assert removal.reason is None
    assert removal.sha256 == full_digest(copy)


def test_a_file_longer_on_either_side_is_not_identical(tmp_path: Path) -> None:
    """The byte comparison reads both files to their very end."""
    short, long = tmp_path / "short", tmp_path / "long"
    short.write_bytes(b"same")
    long.write_bytes(b"same+")
    assert identical_digest(short, long) is None
    assert identical_digest(long, short) is None


def test_every_blocker(tmp_path: Path) -> None:
    """Missing keeper, missing copy, changed size, different bytes: all block."""
    keeper, copy = tmp_path / "keeper", tmp_path / "copy"
    assert removal_blocker(keeper, copy, 4) is not None
    keeper.write_bytes(b"same")
    assert removal_blocker(keeper, copy, 4) == "the file no longer exists"
    copy.write_bytes(b"longer")
    assert removal_blocker(keeper, copy, 4) == "a file changed since the audit"
    copy.write_bytes(b"diff")
    assert removal_blocker(keeper, copy, 4) == "the files are no longer identical"


def test_one_file_reached_through_two_paths_is_never_deleted(tmp_path: Path) -> None:
    """A hard link, or a folder mounted twice, is the kept file itself: kept."""
    keeper, alias = tmp_path / "keeper", tmp_path / "alias"
    keeper.write_bytes(b"same")
    alias.hardlink_to(keeper)
    assert removal_blocker(keeper, alias, 4) == (
        "it is the kept copy itself, seen through another path"
    )


def test_a_burst_shot_moves_only_while_a_kept_shot_is_left(tmp_path: Path) -> None:
    """Every kept shot gone: the shot set aside stays; one left: it may move."""
    kept, aside = tmp_path / "kept.jpg", tmp_path / "aside.jpg"
    aside.write_bytes(b"shot")
    stat = aside.stat()
    candidate = MediaFile(aside, stat.st_size, stat.st_mtime_ns, MediaKind.IMAGE)
    shot = MediaFile(kept, 4, 0, MediaKind.IMAGE)
    assert burst_blocker((shot,), candidate) == "no shot kept from its series is left"
    kept.write_bytes(b"best")
    assert burst_blocker((shot,), candidate) is None
