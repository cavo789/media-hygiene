"""A video, its smaller re-encoded copy and another video, written by ffmpeg."""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from tests.support.media import VIDEO_TAGS, encode

if TYPE_CHECKING:
    from pathlib import Path

ORIGINAL: Final = "c/Family Videos/Plage.mp4"
COPY: Final = "c/Users/Public/WhatsApp/VID-20210714-WA0003.mp4"
OTHER: Final = "c/Family Videos/Fractale.mp4"
ZOOM: Final = "mandelbrot=size=320x240:rate=15"
PATTERN: Final = "testsrc2=size=320x240:rate=15"


def write_near_videos(data: Path) -> None:
    """Write the original, its re-encoded copy and an unrelated video.

    Args:
        data: Directory standing for the /data mount point.
    """
    lavfi = ("-f", "lavfi", "-t", "3", "-pix_fmt", "yuv420p", *VIDEO_TAGS)
    encode(data / ORIGINAL, *lavfi[:2], "-i", ZOOM, *lavfi[2:])
    copy = ("-vf", "scale=160:120", "-r", "10", "-map_metadata", "-1")
    encode(data / COPY, "-i", str(data / ORIGINAL), *copy)
    encode(data / OTHER, *lavfi[:2], "-i", PATTERN, *lavfi[2:])
