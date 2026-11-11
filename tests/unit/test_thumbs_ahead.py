"""Thumbnails made at the end of the audit: the same files the pages would make."""

from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.report.preview_ahead import made_ahead
from media_hygiene.report.preview_cache import PreviewJob, cached_preview
from media_hygiene.search.thumbs import GRID_EDGE
from media_hygiene.services import thumbs_ahead
from media_hygiene.services.thumbs_ahead import AheadRun, pictures

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.scan.progress import Step


class _Counted:
    """A progress sink that counts what it is told."""

    def __init__(self) -> None:
        """Nothing counted yet."""
        self.steps: list[Step] = []
        self.advanced = 0

    def start(self, step: Step, _total: int | None) -> None:
        """Record the step."""
        self.steps.append(step)

    def advance(self, _weight: int = 1) -> None:
        """Count one file."""
        self.advanced += 1

    def current(self, _text: str) -> None:
        """Ignored."""

    def stop(self) -> None:
        """Ignored."""


class _Runtime:
    """The two things the step reads of the runtime."""

    def __init__(self, folder: Path | None) -> None:
        """Keep the cache folder."""
        self.previews_dir = folder

    @staticmethod
    def executor_factory() -> ThreadPoolExecutor:
        """A thread pool: the test needs no process."""
        return ThreadPoolExecutor(2)


def _photos(tmp_path: Path, count: int) -> list[Path]:
    """Small photos, and a video the step must leave out."""
    (tmp_path / "clip.mp4").write_bytes(b"video")
    paths = []
    for number in range(count):
        path = tmp_path / f"IMG_{number}.jpg"
        Image.new("RGB", (640, 480), (number * 40, 30, 30)).save(path)
        paths.append(path)
    return paths


def test_same_thumbnail_as_the_page_would_make(tmp_path: Path) -> None:
    """Made ahead, then read by the page: one file, byte for byte the same."""
    folder = tmp_path / "previews"
    job = PreviewJob(_photos(tmp_path, 1)[0], GRID_EDGE, folder)
    assert made_ahead(job) is True
    (kept,) = folder.iterdir()
    assert (
        cached_preview(job)
        == kept.read_bytes()
        == cached_preview(PreviewJob(job.source, GRID_EDGE, None))
    )
    assert made_ahead(job) is False  # kept already: no second decode
    assert made_ahead(PreviewJob(tmp_path / "gone.jpg", GRID_EDGE, folder)) is False
    assert made_ahead(PreviewJob(job.source, GRID_EDGE, None)) is False


def test_every_photo_once_then_nothing(tmp_path: Path) -> None:
    """The first audit makes them all, the next one none; videos are left out."""
    paths = pictures([*_photos(tmp_path, 3), tmp_path / "clip.mp4"])
    assert len(paths) == 3
    runtime = _Runtime(tmp_path / "previews")
    progress = _Counted()
    run = AheadRun(progress, lambda: False)
    first = thumbs_ahead.make_thumbnails(runtime, paths, run)  # type: ignore[arg-type]
    assert first is not None
    assert (first.made, first.left) == (3, 0)
    assert progress.advanced == 3
    assert "Ctrl+C" in progress.steps[0].hint
    again = thumbs_ahead.make_thumbnails(runtime, paths, run)  # type: ignore[arg-type]
    assert again is not None
    assert (again.made, again.left) == (0, 0)


def test_ctrl_c_leaves_the_rest_for_the_pages(tmp_path: Path) -> None:
    """A stop asked at once: nothing started, every photo left."""
    paths = _photos(tmp_path, 3)
    run = AheadRun(_Counted(), lambda: True)
    outcome = thumbs_ahead.make_thumbnails(
        _Runtime(tmp_path / "previews"),  # type: ignore[arg-type]
        paths,
        run,
    )
    assert outcome is not None
    assert (outcome.made, outcome.left) == (0, 3)


def test_nothing_without_a_kept_cache(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No persistent cache, or no photo: the step does not even start."""
    monkeypatch.setattr(thumbs_ahead, "made_ahead", None)
    run = AheadRun(_Counted(), lambda: False)
    runtime = _Runtime(None)
    assert thumbs_ahead.make_thumbnails(runtime, [tmp_path], run) is None  # type: ignore[arg-type]
    runtime = _Runtime(tmp_path)
    assert thumbs_ahead.make_thumbnails(runtime, [], run) is None  # type: ignore[arg-type]
