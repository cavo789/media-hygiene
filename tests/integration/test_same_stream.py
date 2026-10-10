"""A video copied with new metadata only: the usual rules keep one, not the larger."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from tests.support.cli import run
from tests.support.media import FFMPEG, VIDEO_TAGS, encode

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

ORIGINAL: Final = "c/Fête 2015/20150704_101010.mp4"
RENAMED: Final = "c/Exports/162.mp4"
ZOOM: Final = "mandelbrot=size=320x240:rate=15"

pytestmark = pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the videos")


@pytest.fixture
def renamed(cli: CliRunner, locations: Locations) -> CliRunner:
    """The original, and a renamed copy whose metadata alone grew (a rating set)."""
    data = locations.data_dir
    lavfi = ("-f", "lavfi", "-t", "3", "-i", ZOOM, "-pix_fmt", "yuv420p")
    encode(data / ORIGINAL, *lavfi, *VIDEO_TAGS)
    rating = ("-metadata", "comment=" + "rated 5 stars " * 20)
    copy = ("-i", str(data / ORIGINAL), "-c", "copy", *VIDEO_TAGS, *rating)
    encode(data / RENAMED, *copy)
    return cli


def test_the_original_is_kept(renamed: CliRunner, locations: Locations) -> None:
    """The larger copy is the renamed one: the folder and name someone chose win."""
    data = locations.data_dir
    assert (data / RENAMED).stat().st_size > (data / ORIGINAL).stat().st_size
    result = run(renamed, "clean", "--yes", "--tier", "near")
    assert result.exit_code == 0, result.output
    assert (data / ORIGINAL).is_file()
    assert not (data / RENAMED).exists()
    report = next(locations.reports_dir.glob("*-clean"))
    page = (report / "near.html").read_text()
    assert "Same picture and sound as the kept video" in page
    assert 'src="file:///C:/Exports/162.mp4"' in page
    assert 'id="bursts"' not in page
