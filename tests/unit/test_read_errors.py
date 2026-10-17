"""A read the disk or the cloud failed is never a broken file (0222)."""

from __future__ import annotations

import asyncio
import errno
import os
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.index.repository import FactsRepository
from media_hygiene.scan import image_check, video_check
from media_hygiene.scan.broken import BrokenFileFinder
from media_hygiene.scan.deps import IntegrityTools, ScanDeps
from media_hygiene.scan.file_check import Need, need_of
from media_hygiene.scan.image_check import inspect_image
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.progress import NullProgress
from media_hygiene.scan.read_errors import (
    ReadFailedError,
    is_read_error,
    is_read_error_message,
    is_stored_read_error,
)
from media_hygiene.scan.tool_run import ToolRun
from media_hygiene.scan.video_check import probe_video
from tests.support.media import MediaFactory

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.scan.models import BrokenFile
    from media_hygiene.scan.read_errors import UnreadFile

_EIO = OSError(errno.EIO, os.strerror(errno.EIO))


def listed(path: Path, kind: MediaKind = MediaKind.IMAGE) -> MediaFile:
    """The file as the scan lists it."""
    stat = path.stat()
    return MediaFile(path, stat.st_size, stat.st_mtime_ns, kind)


def failing_read(path: Path, limit: int) -> bytes | None:
    """Stand for a disk that fails while the file is read."""
    del path, limit
    raise _EIO


def truncated_read(path: Path, limit: int) -> bytes | None:
    """Stand for Pillow's own error: an `OSError` without errno."""
    del path, limit
    message = "image file is truncated"
    raise OSError(message)


def tool_run(stderr: str) -> object:
    """A fake `run_tool` printing `stderr` and failing."""

    async def run(command: Sequence[str], seconds: float) -> ToolRun:
        del command, seconds
        return ToolRun(1, b"", stderr.encode())

    return run


def check_one(
    file: MediaFile, repository: FactsRepository
) -> tuple[tuple[BrokenFile, ...], tuple[UnreadFile, ...]]:
    """Run the integrity pass on one image, in threads."""
    with ThreadPoolExecutor(max_workers=1) as executor:
        finder = BrokenFileFinder(
            ScanDeps(repository, NullProgress()), IntegrityTools(executor, None)
        )
        found = asyncio.run(finder.find([file]))
    return found.broken, found.unread


@pytest.mark.parametrize(
    ("error", "expected"),
    [
        (OSError(errno.EIO, "Input/output error"), True),
        (FileNotFoundError(errno.ENOENT, "No such file"), True),
        (OSError("image file is truncated"), False),
        (SyntaxError("not a JPEG"), False),
        (ValueError("bad"), False),
    ],
)
def test_read_error_or_decoding_failure(error: Exception, *, expected: bool) -> None:
    """An `OSError` with an errno is a failed read; everything else a damaged file."""
    assert is_read_error(error) is expected


def test_tool_messages() -> None:
    """`ffprobe`'s system messages are read errors; its decoding messages are not."""
    assert is_read_error_message("/data/c/a.mp4: Input/output error")
    assert is_read_error_message("/data/c/a.mp4: Connection timed out\n")
    assert not is_read_error_message(
        "/data/c/a.mp4: Invalid data found when processing input"
    )
    assert not is_read_error_message("moov atom not found")


def test_stored_verdicts_of_older_versions() -> None:
    """A verdict stored after a failed read is recognised, a decoding one not."""
    assert is_stored_read_error(
        "OSError: [Errno 5] Input/output error: '/data/c/a.jpg'"
    )
    assert is_stored_read_error("/data/c/a.mp4: Input/output error")
    assert not is_stored_read_error("OSError: image file is truncated")
    assert not is_stored_read_error("moov atom not found")


def test_read_failure_detail() -> None:
    """The failure carries the decoder's text, or nothing."""
    assert ReadFailedError("boom").detail == "boom"
    assert not ReadFailedError().detail


def test_failed_read_is_not_broken_nor_stored(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An EIO while decoding: not broken, listed, and nothing stored in the index."""
    file = listed(MediaFactory(tmp_path).image("a.jpg"))
    monkeypatch.setattr(image_check, "read_whole", failing_read)
    assert inspect_image(file.path).unread
    with FactsRepository.open(None) as repository:
        broken, unread = check_one(file, repository)
        assert not broken
        assert [item.file for item in unread] == [file]
        assert "Errno 5" in unread[0].detail
        assert not repository.get(file).integrity_checked


def test_truncated_image_is_broken_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Pillow's own `OSError` (no errno) still makes the file broken, stored."""
    file = listed(MediaFactory(tmp_path).image("a.jpg"))
    monkeypatch.setattr(image_check, "read_whole", truncated_read)
    with FactsRepository.open(None) as repository:
        broken, unread = check_one(file, repository)
        assert not unread
        assert [item.reason for item in broken] == [BrokenReason.UNREADABLE_IMAGE]
        assert repository.get(file).broken_reason is BrokenReason.UNREADABLE_IMAGE


def test_ffprobe_read_error_is_not_broken(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`ffprobe` ending on `Input/output error`: the video was not read."""
    video = tmp_path / "a.mp4"
    video.write_bytes(b"video")
    monkeypatch.setattr(
        video_check, "run_tool", tool_run(f"{video}: Input/output error\n")
    )
    probe = asyncio.run(probe_video(video, "ffprobe"))
    assert probe.unread
    assert probe.problem == f"{video}: Input/output error"


def test_other_ffprobe_failure_is_broken_as_before(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Any other `ffprobe` failure still makes the video broken."""
    video = tmp_path / "a.mp4"
    video.write_bytes(b"video")
    monkeypatch.setattr(video_check, "run_tool", tool_run("moov atom not found\n"))
    probe = asyncio.run(probe_video(video, "ffprobe"))
    assert not probe.unread
    assert probe.problem == "moov atom not found"


def test_older_read_error_verdict_is_checked_again(tmp_path: Path) -> None:
    """A file an older version stored broken after a failed read is checked again."""
    video = tmp_path / "a.mp4"
    video.write_bytes(b"video")
    file = listed(video, MediaKind.VIDEO)
    with FactsRepository.open(None) as repository:
        known = repository.get(file)
        failed = known.with_integrity(
            BrokenReason.UNREADABLE_VIDEO, f"{video}: Input/output error"
        )
        assert need_of(file, failed) is Need.CHECK
        damaged = known.with_integrity(
            BrokenReason.UNREADABLE_VIDEO, "moov atom not found"
        )
        assert need_of(file, damaged) is Need.NOTHING
