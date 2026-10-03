"""Re-encoded videos, from real files: listed, moved only with --tier near, undone."""

from __future__ import annotations

import subprocess
from typing import TYPE_CHECKING, Final

import pytest

from tests.support.cli import run
from tests.support.media import FFMPEG, VIDEO_TAGS

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

ORIGINAL: Final = "c/Family Videos/Plage.mp4"
COPY: Final = "c/Users/Public/WhatsApp/VID-20210714-WA0003.mp4"
OTHER: Final = "c/Family Videos/Fractale.mp4"
ZOOM: Final = "mandelbrot=size=320x240:rate=15"
PATTERN: Final = "testsrc2=size=320x240:rate=15"

pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the videos")


def encode(target: Path, *arguments: str) -> None:
    """Run ffmpeg quietly, writing `target`.

    Args:
        target: The video written.
        *arguments: Its inputs and options.
    """
    target.parent.mkdir(parents=True, exist_ok=True)
    command = [FFMPEG or "ffmpeg", "-loglevel", "error", "-y", *arguments]
    subprocess.run([*command, str(target)], check=True)  # noqa: S603 - trusted


@pytest.fixture
def videos(cli: CliRunner, locations: Locations) -> CliRunner:
    """The demo tree, plus a video, its smaller re-encoded copy and another video."""
    data = locations.data_dir
    lavfi = ("-f", "lavfi", "-t", "3", "-pix_fmt", "yuv420p", *VIDEO_TAGS)
    encode(data / ORIGINAL, *lavfi[:2], "-i", ZOOM, *lavfi[2:])
    copy = ("-vf", "scale=160:120", "-r", "10", "-map_metadata", "-1")
    encode(data / COPY, "-i", str(data / ORIGINAL), *copy)
    encode(data / OTHER, *lavfi[:2], "-i", PATTERN, *lavfi[2:])
    return cli


def test_the_audit_lists_the_copy(videos: CliRunner, locations: Locations) -> None:
    """Counted in the summary, explained in a tip, shown in the report."""
    output = run(videos, "audit").output
    assert "Re-encoded videos (moved only with --tier near)" in output
    assert "Re-encoded videos are in the HTML report" in output
    report = next(locations.reports_dir.glob("*-audit/report.html")).read_text()
    assert "VID-20210714-WA0003.mp4" in report
    assert "Fractale.mp4" not in report


def test_the_copy_moves_only_with_the_tier(
    videos: CliRunner, locations: Locations
) -> None:
    """A plain clean keeps it; --tier near quarantines it; undo brings it back."""
    data = locations.data_dir
    assert run(videos, "clean", "--yes").exit_code == 0
    assert (data / COPY).is_file()
    assert run(videos, "undo").exit_code == 0
    near = run(videos, "clean", "--yes", "--tier", "near")
    assert near.exit_code == 0, near.output
    assert not (data / COPY).exists()
    assert (data / ORIGINAL).is_file()
    assert (data / OTHER).is_file()
    assert run(videos, "undo").exit_code == 0
    assert (data / COPY).is_file()
