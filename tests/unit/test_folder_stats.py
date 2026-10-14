"""A folder read again: only its new names are `stat`ed, in parallel batches (0153)."""

from __future__ import annotations

import asyncio
import os
import time
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

from media_hygiene.scan import folder_stats
from media_hygiene.scan.filters import ScanFilters
from media_hygiene.scan.folder_cache import CachedEntry, WalkSetup, cached_entry
from media_hygiene.scan.progress import NullProgress
from media_hygiene.scan.walker import Walk, walk

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    import pytest

    from media_hygiene.scan.folder_cache import CachedStat

_FILTERS: Final = ScanFilters()
_SLOW_SECONDS: Final = 0.002
_MANY: Final = 600


def _walk(root: Path, setup: WalkSetup | None = None) -> Walk:
    """Walk the tree, trusting what `setup` holds."""
    return asyncio.run(walk((root,), setup or WalkSetup(_FILTERS), NullProgress()))


def _changed(folder: Path) -> None:
    """Add a photo, and move the folder's time on as a slow file system may not."""
    (folder / "new.jpg").write_bytes(b"n" * 3)
    stat = folder.stat()
    os.utime(folder, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))


def _sizes(found: Walk) -> dict[str, int]:
    """The size of each file found, by name."""
    return {file.path.name: file.size for file in found.files}


def test_a_changed_folder_keeps_the_stats_of_its_known_files(tmp_path: Path) -> None:
    """A known name keeps its last `stat`; a new name is `stat`ed.

    A file rewritten in place waits for the full check, as in an unchanged folder.
    """
    (tmp_path / "a.jpg").write_bytes(b"x" * 10)
    first = _walk(tmp_path)
    (tmp_path / "a.jpg").write_bytes(b"y" * 99)
    _changed(tmp_path)
    recent = WalkSetup(_FILTERS, first.listings, datetime.now(UTC) - timedelta(days=7))
    assert _sizes(_walk(tmp_path, recent)) == {"a.jpg": 10, "new.jpg": 3}
    full = WalkSetup(_FILTERS, first.listings, None)  # audit --full
    assert _sizes(_walk(tmp_path, full)) == {"a.jpg": 99, "new.jpg": 3}
    old = WalkSetup(_FILTERS, first.listings, datetime.now(UTC) + timedelta(seconds=1))
    assert _sizes(_walk(tmp_path, old)) == {"a.jpg": 99, "new.jpg": 3}


def test_the_files_of_a_big_folder_are_stated_in_parallel(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """600 files at 2 ms each: well under the 1.2 s of one thread."""
    for index in range(_MANY):
        (tmp_path / f"{index}.jpg").write_bytes(b"x")

    def slow(entry: os.DirEntry[str], kept: Mapping[str, CachedStat]) -> CachedEntry:
        time.sleep(_SLOW_SECONDS)
        return cached_entry(entry, kept)

    monkeypatch.setattr(folder_stats, "cached_entry", slow)
    started = time.monotonic()
    found = _walk(tmp_path)
    assert len(found.files) == _MANY
    assert time.monotonic() - started < _MANY * _SLOW_SECONDS / 2


def test_a_folder_changing_every_day_is_still_read_in_full(tmp_path: Path) -> None:
    """Kept stats keep the date of the full reading they come from."""
    (tmp_path / "a.jpg").write_bytes(b"x" * 10)
    first = _walk(tmp_path)
    _changed(tmp_path)
    since = datetime.now(UTC) - timedelta(days=7)
    second = _walk(tmp_path, WalkSetup(_FILTERS, first.listings, since))
    assert second.listings[tmp_path].listed_at == first.listings[tmp_path].listed_at


def test_a_file_saved_as_a_new_file_is_stated_again(tmp_path: Path) -> None:
    """An editor writes a new file and renames it over the old one: a new inode."""
    (tmp_path / "a.jpg").write_bytes(b"x" * 10)
    first = _walk(tmp_path)
    (tmp_path / "saving.tmp").write_bytes(b"y" * 99)
    (tmp_path / "saving.tmp").replace(tmp_path / "a.jpg")
    _changed(tmp_path)
    recent = WalkSetup(_FILTERS, first.listings, datetime.now(UTC) - timedelta(days=7))
    assert _sizes(_walk(tmp_path, recent)) == {"a.jpg": 99, "new.jpg": 3}
