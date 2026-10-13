"""The walk takes unchanged folders from the last listing; every change is seen."""

from __future__ import annotations

import asyncio
import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from media_hygiene.scan.filters import ScanFilters
from media_hygiene.scan.folder_cache import WalkSetup
from media_hygiene.scan.progress import NullProgress
from media_hygiene.scan.walker import Walk, walk

if TYPE_CHECKING:
    from pathlib import Path

_FILTERS = ScanFilters()


def _tree(root: Path) -> None:
    """Two folders of photos."""
    for name in ("2019/a.jpg", "2019/b.jpg", "2020/c.jpg"):
        (root / name).parent.mkdir(parents=True, exist_ok=True)
        (root / name).write_bytes(b"x" * 10)


def _again(root: Path, first: Walk, since: datetime | None) -> Walk:
    """Walk again, trusting the listings of the first walk listed after `since`."""
    setup = WalkSetup(_FILTERS, first.listings, since)
    return asyncio.run(walk((root,), setup, NullProgress()))


def _names(found: Walk) -> set[str]:
    """The names of the files found."""
    return {file.path.name for file in found.files}


@pytest.fixture(name="first")
def first_fixture(tmp_path: Path) -> Walk:
    """The tree, walked once in full."""
    _tree(tmp_path)
    return asyncio.run(walk((tmp_path,), WalkSetup(_FILTERS), NullProgress()))


def test_an_unchanged_tree_is_not_listed_again(
    tmp_path: Path, first: Walk, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Every folder reused: no `scandir`, the same files and sizes."""
    listed: list[str] = []
    real = os.scandir

    def scandir(folder: str) -> object:
        listed.append(str(folder))
        return real(folder)

    monkeypatch.setattr("media_hygiene.scan.walker.os.scandir", scandir)
    again = _again(tmp_path, first, datetime.now(UTC) - timedelta(days=7))
    assert not listed
    assert again.reused == len(first.visited) == 3
    assert {(f.path, f.size) for f in again.files} == {
        (f.path, f.size) for f in first.files
    }


def test_added_removed_and_renamed_files_are_seen(tmp_path: Path, first: Walk) -> None:
    """Each change touches its folder's time: that folder is read again."""
    (tmp_path / "2019" / "d.jpg").write_bytes(b"new")
    (tmp_path / "2020" / "c.jpg").rename(tmp_path / "2020" / "e.jpg")
    (tmp_path / "2019" / "a.jpg").unlink()
    _settle(tmp_path / "2019", tmp_path / "2020")
    again = _again(tmp_path, first, datetime.now(UTC) - timedelta(days=7))
    assert _names(again) == {"b.jpg", "d.jpg", "e.jpg"}
    assert again.reused == 1  # the root only
    assert set(again.listings) == {tmp_path / "2019", tmp_path / "2020"}


def test_a_file_rewritten_in_place_waits_for_the_full_check(
    tmp_path: Path, first: Walk
) -> None:
    """Same name, same folder time: old size until the listing is too old to trust."""
    (tmp_path / "2019" / "a.jpg").write_bytes(b"y" * 99)
    size = {f.path.name: f.size for f in _again(tmp_path, first, None).files}
    assert size["a.jpg"] == 99
    recent = datetime.now(UTC) - timedelta(days=7)
    trusted = {f.path.name: f.size for f in _again(tmp_path, first, recent).files}
    assert trusted["a.jpg"] == 10
    future = datetime.now(UTC) + timedelta(seconds=1)  # every listing is older
    full = {f.path.name: f.size for f in _again(tmp_path, first, future).files}
    assert full["a.jpg"] == 99


def _settle(*folders: Path) -> None:
    """Move the folders' times on, as a slow file system might not have yet."""
    for folder in folders:
        stat = folder.stat()
        os.utime(folder, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
