"""Previews kept in the cache: rendered once per file version and size."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.report.preview_cache import (
    PreviewJob,
    cached_preview,
    trim_previews,
)

if TYPE_CHECKING:
    from pathlib import Path

_EDGE = 360
_KEPT = b"cached"


def photo(tmp_path: Path) -> Path:
    """A small red photo."""
    path = tmp_path / "IMG_1.jpg"
    Image.new("RGB", (800, 600), (200, 30, 30)).save(path)
    return path


def test_rendered_kept_then_read_back(tmp_path: Path) -> None:
    """The second call reads the kept file; another size is another preview."""
    folder = tmp_path / "cache" / "previews"
    job = PreviewJob(photo(tmp_path), _EDGE, folder)
    first = cached_preview(job)
    assert first is not None
    assert first.startswith(b"\xff\xd8")
    (kept,) = folder.iterdir()
    kept.write_bytes(_KEPT)
    assert cached_preview(job) == _KEPT
    assert cached_preview(PreviewJob(job.source, 160, folder)) != _KEPT
    assert len(list(folder.iterdir())) == 2


def test_a_file_rewritten_gets_a_new_preview(tmp_path: Path) -> None:
    """A new modification time: the kept preview no longer holds."""
    folder = tmp_path / "previews"
    job = PreviewJob(photo(tmp_path), _EDGE, folder)
    cached_preview(job)
    (kept,) = folder.iterdir()
    kept.write_bytes(_KEPT)
    stat = job.source.stat()
    os.utime(job.source, ns=(stat.st_atime_ns, stat.st_mtime_ns + 10**9))
    assert cached_preview(job) != _KEPT


def test_without_a_cache_nothing_is_kept(tmp_path: Path) -> None:
    """No folder: rendered each time; an unwritable folder is no error."""
    source = photo(tmp_path)
    assert cached_preview(PreviewJob(source, _EDGE, None)) is not None
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert cached_preview(PreviewJob(source, _EDGE, blocker / "previews")) is not None
    assert sorted(path.name for path in tmp_path.iterdir()) == ["IMG_1.jpg", "file"]


def test_nothing_for_what_is_no_picture(tmp_path: Path) -> None:
    """A video: no preview, and remembered as such; a missing file: nothing kept."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a picture")
    folder = tmp_path / "previews"
    assert cached_preview(PreviewJob(tmp_path / "gone.jpg", _EDGE, folder)) is None
    assert not folder.exists()
    assert cached_preview(PreviewJob(video, _EDGE, folder)) is None
    (marker,) = folder.iterdir()
    assert not marker.read_bytes()
    assert cached_preview(PreviewJob(video, _EDGE, folder)) is None


def test_trimmed_least_recently_used_first(tmp_path: Path) -> None:
    """Beyond the bound, the oldest previews go until well below it."""
    folder = tmp_path / "previews"
    folder.mkdir()
    for number in range(10):
        kept = folder / f"{number}.jpg"
        kept.write_bytes(b"x" * 100)
        os.utime(kept, ns=(number * 10**9, number * 10**9))
    assert trim_previews(folder, 2_000) == 0
    assert trim_previews(folder, 500) == 6
    assert sorted(path.name for path in folder.iterdir()) == [
        "6.jpg",
        "7.jpg",
        "8.jpg",
        "9.jpg",
    ]
    assert trim_previews(None, 500) == 0
    assert trim_previews(tmp_path / "none", 500) == 0
