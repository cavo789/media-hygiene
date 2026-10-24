"""Synthetic clips for the tests of `shrink`: an old camera's MJPEG, a phone's H.264.

Encoded by the test with `ffmpeg` (`testsrc2` and a tone), never a real video.
"""

from __future__ import annotations

import os
import shutil
import subprocess
from typing import TYPE_CHECKING, Final

import pytest
from typer.testing import CliRunner

from tests.support.cli import point_mounts, run

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations

FFMPEG: Final = shutil.which("ffmpeg") or "ffmpeg"
MTIME: Final = 1_436_868_000_000_000_000  # 2015-07-14
CAMERA: Final = "c/Videos/Camera/clip.avi"
PHONE: Final = "c/Videos/Phone/phone.mp4"
KEPT: Final = "c/Videos/Kept/kept.avi"
MJPEG: Final = ("-c:v", "mjpeg", "-q:v", "2", "-c:a", "pcm_s16le")
_TAGS: Final = (
    "-metadata",
    "creation_time=2015-07-14T10:00:00Z",
    "-metadata",
    "location=+50.8466+004.3528/",
)

NEEDS_X264: Final = pytest.mark.skipif(
    subprocess.run(  # noqa: S603  # a fixed command
        (FFMPEG, "-hide_banner", "-encoders"), capture_output=True, check=False
    ).stdout.find(b"libx264")
    < 0,
    reason="this ffmpeg cannot encode H.264",
)


def clip(path: Path, codec: tuple[str, ...], tone: int = 440) -> Path:
    """Encode a 3 s clip with sound and a camera's tags, dated 2015.

    Args:
        path: Where.
        codec: The `ffmpeg` options of its codecs.
        tone: The sound's frequency: two clips with another tone differ.

    Returns:
        The clip.
    """
    path.parent.mkdir(parents=True, exist_ok=True)
    picture = ("-f", "lavfi", "-i", "testsrc2=size=320x240:rate=25:duration=3")
    sound = ("-f", "lavfi", "-i", f"sine=frequency={tone}:duration=3")
    command = (FFMPEG, "-v", "error", "-y", *picture, *sound, *codec, *_TAGS, str(path))
    subprocess.run(command, check=True)  # noqa: S603  # fixed arguments
    os.utime(path, ns=(MTIME, MTIME))
    return path


def camera_tree(locations: Locations) -> None:
    """A camera's MJPEG clip with its sidecar, a phone's H.264, one protected clip.

    Args:
        locations: The test mount points.
    """
    camera = clip(locations.data_dir / CAMERA, MJPEG)
    camera.with_name("clip.avi.xmp").write_text("<x:xmpmeta/>")
    clip(locations.data_dir / KEPT, MJPEG, tone=880)  # not a copy of the camera's
    clip(locations.data_dir / PHONE, ("-c:v", "libx264", "-c:a", "aac"))
    locations.config_file.write_text(
        "[folders]\nprotected = ['C:\\Videos\\Kept']\n", encoding="utf-8"
    )


def audited(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """The mounts pointed to the test's folders, `camera_tree` written and audited.

    Args:
        locations: The test mount points.
        monkeypatch: Pytest monkeypatch fixture.

    Returns:
        The runner.
    """
    point_mounts(locations, monkeypatch)
    camera_tree(locations)
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    return runner
