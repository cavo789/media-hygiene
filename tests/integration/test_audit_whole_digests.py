"""After an audit every photo and video has a SHA-256, kept while it is true (0634)."""

from __future__ import annotations

import os
import shutil
import sqlite3
from contextlib import closing
from typing import TYPE_CHECKING

import pytest

from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.media import FFMPEG, MediaFactory
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg is not installed")


def audit(locations: Locations) -> None:
    """Run an audit walking every folder: an in-place write leaves its time."""
    runtime = make_runtime(locations, {"scan": {"full_check_days": 0}})
    AuditService(runtime, NullProgress()).run()


def stored(locations: Locations) -> dict[str, str | None]:
    """The SHA-256 the index holds, by file name."""
    with closing(sqlite3.connect(locations.index_file)) as connection:
        rows = connection.execute("SELECT path, full_digest FROM files").fetchall()
    return {path.rsplit("/", 1)[-1]: digest for path, digest in rows}


def reads(monkeypatch: pytest.MonkeyPatch) -> list[str]:
    """Record the names of the files the audit reads whole from now on."""
    read: list[str] = []

    def counted(path: Path) -> str:
        read.append(path.name)
        return full_digest(path)

    monkeypatch.setattr("media_hygiene.scan.exact.full_digest", counted)
    return read


@pytest.fixture
def video(locations: Locations) -> Path:
    """A video of unique size, audited once."""
    made = MediaFactory(locations.data_dir).video("c/Photos/seul.mp4")
    audit(locations)
    return made


def test_a_video_of_unique_size_gets_its_digest(
    locations: Locations, video: Path
) -> None:
    """The refusal of Tag can end: a video alone of its size is read once."""
    assert stored(locations)[video.name] == full_digest(video)


def test_an_unchanged_video_is_not_read_again(
    locations: Locations, video: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The digest is paid once."""
    read = reads(monkeypatch)
    audit(locations)
    assert video.name not in read


def test_a_rename_keeps_the_digest_without_reading(
    locations: Locations, video: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rename in Explorer: the row follows the file."""
    before = full_digest(video)
    read = reads(monkeypatch)
    video.rename(video.with_name("renomme.mp4"))
    audit(locations)
    assert not read
    assert stored(locations) == {"renomme.mp4": before}


def test_a_move_keeps_the_digest_without_reading(
    locations: Locations, video: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A move to another folder: the row follows the file."""
    before = full_digest(video)
    read = reads(monkeypatch)
    folder = video.parent / "ailleurs"
    folder.mkdir()
    video.rename(folder / video.name)
    audit(locations)
    assert not read
    assert stored(locations)[video.name] == before


def test_an_in_place_write_gives_a_new_digest(
    locations: Locations, video: Path
) -> None:
    """Same size, other bytes, a new time: the old digest is not trusted."""
    before = full_digest(video)
    data = bytearray(video.read_bytes())
    data[-1] ^= 0xFF
    stat = video.stat()
    video.write_bytes(data)
    os.utime(video, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    audit(locations)
    assert stored(locations)[video.name] == full_digest(video) != before


def test_a_copy_keeping_the_time_has_its_own_row(
    locations: Locations, video: Path
) -> None:
    """A copy keeping the mtime, the original still there: both rows hold it."""
    copy = video.with_name("copie.mp4")
    shutil.copy2(video, copy)
    audit(locations)
    found = stored(locations)
    assert found[copy.name] == found[video.name] == full_digest(video)


def test_a_touch_reads_it_again_to_the_same_digest(
    locations: Locations, video: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A new time alone proves nothing: read again, same digest."""
    before = full_digest(video)
    stat = video.stat()
    os.utime(video, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    read = reads(monkeypatch)
    audit(locations)
    assert video.name in read
    assert stored(locations)[video.name] == before
