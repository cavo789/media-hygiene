"""A video's preview: one frame, kept in the cache like a photo's (TODO 0373)."""

from __future__ import annotations

import hashlib
import io
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
