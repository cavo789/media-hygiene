"""The previews of the search grid: rendered once, then read from the cache."""

from __future__ import annotations

from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.index.descriptions import PhotoVersion
from media_hygiene.search.thumbs import GridPreview, grid_preview

if TYPE_CHECKING:
    from pathlib import Path


def test_rendered_kept_then_read_back(tmp_path: Path) -> None:
    """The second call reads the cached file; a new version gets a new preview."""
    photo = tmp_path / "IMG_1.jpg"
    Image.new("RGB", (800, 600), (200, 30, 30)).save(photo)
    folder = tmp_path / "cache" / "previews"
    job = GridPreview(PhotoVersion(photo, 1, 2), folder)
    first = grid_preview(job)
    assert first is not None
    assert first.startswith(b"\xff\xd8")
    (kept,) = folder.iterdir()
    kept.write_bytes(b"cached")
    assert grid_preview(job) == b"cached"
    assert grid_preview(GridPreview(PhotoVersion(photo, 1, 3), folder)) == first


def test_nothing_for_a_video_and_no_cache_when_unwritable(tmp_path: Path) -> None:
    """No preview of what is no picture; an unwritable cache is no error."""
    video = tmp_path / "clip.mp4"
    video.write_bytes(b"not a picture")
    blocker = tmp_path / "file"
    blocker.write_text("x")
    assert grid_preview(GridPreview(PhotoVersion(video, 1, 1), tmp_path)) is None
    photo = tmp_path / "IMG_2.png"
    Image.new("RGB", (50, 40)).save(photo)
    job = GridPreview(PhotoVersion(photo, 1, 1), blocker / "previews")
    assert grid_preview(job) is not None
