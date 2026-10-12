"""A black and white edit is not a near duplicate of its colour original."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

import pytest

from tests.support.cli import run
from tests.support.media import FFMPEG, VIDEO_TAGS, encode
from tests.support.scenes import Effect, Shot, write_shot

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

SEED: Final = 4242
DATE: Final = "2022:05:26 19:07:48"
COLOUR: Final = "c/Spectacle 2023/Spectacle.jpg"
SMALL: Final = "c/Spectacle 2023/Spectacle (petite).jpg"
GREY: Final = "c/Spectacle 2023/Spectacle N&B.jpg"
CLIP: Final = "c/Spectacle 2023/IMG_1234_1.mp4"
GREY_CLIP: Final = "c/Spectacle 2023/IMG_1234_1_1.mp4"
TESTSRC: Final = "testsrc2=size=320x240:rate=15"


def report_of(locations: Locations) -> str:
    """The near-duplicates page and the CSV of the latest audit."""
    folder = next(locations.reports_dir.glob("*-audit"))
    page = folder / "near.html"
    text = page.read_text() if page.exists() else ""
    return text + (folder / "plan.csv").read_text(encoding="utf-8-sig")


def test_a_black_and_white_photo_stays(cli: CliRunner, locations: Locations) -> None:
    """The smaller colour copy is a near duplicate; the black and white edit is not."""
    data = locations.data_dir
    write_shot(data / COLOUR, Shot(SEED, taken_at=DATE))
    write_shot(data / SMALL, Shot(SEED, size=(240, 180), taken_at=DATE))
    write_shot(data / GREY, Shot(SEED, taken_at=DATE, effect=Effect.MONOCHROME))
    assert run(cli, "audit").exit_code == 0
    text = report_of(locations)
    assert "Spectacle (petite).jpg" in text
    assert "Kept: the highest resolution." in text
    assert "Spectacle N&amp;B.jpg" not in text
    assert "Spectacle N&B.jpg" not in text


@pytest.mark.skipif(FFMPEG is None, reason="ffmpeg writes the videos")
def test_a_black_and_white_video_stays(cli: CliRunner, locations: Locations) -> None:
    """Same frames in grey, same length and size: still not a copy."""
    data = locations.data_dir
    lavfi = ("-f", "lavfi", "-t", "3", "-i", TESTSRC, "-pix_fmt", "yuv420p")
    encode(data / CLIP, *lavfi, *VIDEO_TAGS)
    grey = ("-i", str(data / CLIP), "-vf", "hue=s=0", "-pix_fmt", "yuv420p")
    encode(data / GREY_CLIP, *grey, *VIDEO_TAGS)
    assert run(cli, "audit").exit_code == 0
    assert "IMG_1234_1_1.mp4" not in report_of(locations)
