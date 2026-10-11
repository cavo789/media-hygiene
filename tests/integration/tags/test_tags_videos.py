"""`tags` sees a video by one frame: once per set of copies, never a small one."""

from __future__ import annotations

import asyncio
import io
import shutil
from typing import TYPE_CHECKING

import pytest
from PIL import Image

from media_hygiene.scan.video_still import VideoStill, video_jpeg
from tests.integration.tags.test_tags_command import ASKED, tags_of
from tests.support.cli import run
from tests.support.media import encode

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.fake_ollama import FakeOllama

FFMPEG = shutil.which("ffmpeg")
pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg is not installed")


def write_video(path: Path, size: str) -> Path:
    """Encode two seconds of white, `size` pixels (`640x480`)."""
    source = f"color=c=white:size={size}:rate=10"
    encode(path, "-f", "lavfi", "-i", source, "-t", "2", "-pix_fmt", "yuv420p")
    return path


def test_a_video_is_described_once_by_its_frame(
    cli: CliRunner, fake: FakeOllama, locations: Locations
) -> None:
    """The video and its copy: one frame sent; the small one: never."""
    videos = locations.data_dir / "c" / "Photos" / "Vidéos"
    video = write_video(videos / "Neige.mp4", "640x480")
    shutil.copy2(video, videos / "Neige copie.mp4")
    write_video(videos / "petite.mp4", "160x120")
    assert run(cli, "audit").exit_code == 0
    result = run(cli, "tags", "--yes")
    assert result.exit_code == 0, result.output
    assert fake.described() == ASKED + 1
    for name in ("Neige.mp4", "Neige copie.mp4"):
        assert tags_of(locations, f"Vidéos/{name}")["vision"] == ["snow"]
    assert "vision" not in tags_of(locations, "Vidéos/petite.mp4")
    asked = len(fake.calls)
    assert run(cli, "tags").exit_code == 0
    assert len(fake.calls) == asked


@pytest.mark.parametrize(
    ("size", "expected"), [("640x480", (320, 240)), ("480x640", (240, 320))]
)
def test_the_frame_keeps_its_proportions(
    tmp_path: Path, size: str, expected: tuple[int, int]
) -> None:
    """The longer side shrunk to the edge, the other one in proportion."""
    video = write_video(tmp_path / "clip.mp4", size)
    landscape = expected[0] > expected[1]
    jpeg = video_jpeg_now(VideoStill(video, 1.0, landscape, FFMPEG or "ffmpeg"))
    assert jpeg is not None
    with Image.open(io.BytesIO(jpeg)) as picture:
        assert picture.size == expected


def test_an_unreadable_video_gives_no_frame(tmp_path: Path) -> None:
    """Not a video: None, never an error."""
    broken = tmp_path / "broken.mp4"
    broken.write_bytes(b"not a video")
    assert (
        video_jpeg_now(
            VideoStill(broken, 1.0, landscape=True, ffmpeg=FFMPEG or "ffmpeg")
        )
        is None
    )


def video_jpeg_now(still: VideoStill) -> bytes | None:
    """Run `video_jpeg` to the end, 320 pixels."""
    return asyncio.run(video_jpeg(still, 320))
