"""A video's preview: one frame, kept in the cache like a photo's (TODO 0373)."""

from __future__ import annotations

import hashlib
import io
import os
import shutil
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from media_hygiene.report.preview_cache import PreviewJob, cached_preview, preview_key
from media_hygiene.report.thumbnails import jpeg_preview
from tests.support.media import FFMPEG, MediaFactory

if TYPE_CHECKING:
    from pathlib import Path

pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the video")
_EDGE = 80


def test_a_video_gets_a_jpeg_of_one_frame(tmp_path: Path) -> None:
    """The preview is a JPEG, its longer side the edge asked."""
    video = MediaFactory(tmp_path).video("clip.mp4")

    image = jpeg_preview(video, _EDGE)

    assert image is not None
    with Image.open(io.BytesIO(image)) as picture:
        assert picture.format == "JPEG"
        assert picture.size == (_EDGE, 60)


def test_a_second_request_reads_the_cache(tmp_path: Path) -> None:
    """The frame is decoded once: the second answer comes from the cache folder."""
    video = MediaFactory(tmp_path / "data").video("clip.mp4")
    job = PreviewJob(video, _EDGE, tmp_path / "cache")
    first = cached_preview(job)
    (kept,) = (tmp_path / "cache").iterdir()
    kept.write_bytes(b"kept")

    assert first is not None
    assert cached_preview(job) == b"kept"


def test_a_broken_video_has_no_preview(tmp_path: Path) -> None:
    """A file that is no video gives no picture: the page keeps its placeholder."""
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"not a video")

    assert jpeg_preview(broken, _EDGE) is None


def test_an_empty_preview_of_before_0373_is_not_read(tmp_path: Path) -> None:
    """Before 0373 a video was kept as an empty preview: a frame is made instead."""
    video = MediaFactory(tmp_path / "data").video("clip.mp4")
    job = PreviewJob(video, _EDGE, tmp_path / "cache")
    stat = video.stat()
    old = f"1\0{video}\0{stat.st_size}\0{stat.st_mtime_ns}\0{_EDGE}"
    old_name = hashlib.sha256(old.encode()).hexdigest()[:32] + ".jpg"
    (tmp_path / "cache").mkdir()
    (tmp_path / "cache" / old_name).write_bytes(b"")

    assert preview_key(job, stat.st_size, stat.st_mtime_ns) != old_name
    assert cached_preview(job) is not None


def _poisoned(tmp_path: Path) -> tuple[Path, Path]:
    """A video whose kept frame was replaced by a marker: a stale read returns it.

    Args:
        tmp_path: The test's folder.

    Returns:
        The video and the cache folder.
    """
    video = MediaFactory(tmp_path / "data").video("clip.mp4")
    cache = tmp_path / "cache"
    assert cached_preview(PreviewJob(video, _EDGE, cache)) is not None
    (kept,) = cache.iterdir()
    kept.write_bytes(b"stale")
    return video, cache


def test_a_renamed_or_moved_video_is_not_served_the_old_frame(tmp_path: Path) -> None:
    """The frame is named after the path: a rename or a move decodes again (0733)."""
    video, cache = _poisoned(tmp_path)
    renamed = video.rename(video.with_name("renamed.mp4"))
    (tmp_path / "other").mkdir()
    moved = tmp_path / "other" / "clip.mp4"
    shutil.copy2(renamed, moved)

    for path in (renamed, moved):
        assert cached_preview(PreviewJob(path, _EDGE, cache)) not in {None, b"stale"}


def test_a_video_written_in_place_or_touched_is_decoded_again(tmp_path: Path) -> None:
    """New bytes (another size) or only a new time: another frame name (0733)."""
    video, cache = _poisoned(tmp_path)
    job = PreviewJob(video, _EDGE, cache)
    os.utime(video, ns=(0, video.stat().st_mtime_ns + 1_000_000_000))  # `touch`
    assert cached_preview(job) not in {None, b"stale"}

    stamp = video.stat().st_mtime_ns
    video.write_bytes(video.read_bytes() + bytes(64))  # rewritten, its time put back
    os.utime(video, ns=(stamp, stamp))
    assert cached_preview(job) not in {None, b"stale"}


def test_a_copy_keeping_the_time_over_the_video_is_decoded_again(
    tmp_path: Path,
) -> None:
    """`cp -p` of another video (other size, its own time) over the file (0733)."""
    video, cache = _poisoned(tmp_path)
    other = MediaFactory(tmp_path / "other").video("clip.mp4")
    other.write_bytes(other.read_bytes() + bytes(64))
    shutil.copy2(other, video)

    assert cached_preview(PreviewJob(video, _EDGE, cache)) not in {None, b"stale"}
