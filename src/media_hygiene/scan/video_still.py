"""One frame of a video as a JPEG: what a vision model sees of the video.

`ffmpeg` decodes the frame shown in the middle of the video (an accurate seek),
turned upright, its longer side shrunk to the edge asked; the image's `ffmpeg`
writes raw pixels only, so Pillow makes the JPEG. Which side is the longer one
comes from the probe (size and rotation): the filter sets that side, the other one
follows from the bytes written.
"""

from __future__ import annotations

import io
import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from PIL import Image

from media_hygiene.scan.tool_run import run_tool

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.scan.metadata import MediaMetadata

_LOGGER = logging.getLogger(__name__)
MIDDLE: Final = 0.5  # the moment shown, as a share of the length
_CHANNELS: Final = 3
_QUARTER_TURNS: Final = frozenset({90, 270})
_FULL_TURN: Final = 360
_TIMEOUT_SECONDS: Final = 60
_JPEG_QUALITY: Final = 88
_BEFORE_INPUT: Final = ("-nostdin", "-v", "error", "-threads", "1")
_AFTER_INPUT: Final = ("-map", "0:v:0", "-frames:v", "1", "-an", "-sn", "-dn")
_OUTPUT: Final = ("-pix_fmt", "rgb24", "-f", "rawvideo", "pipe:1")


@dataclass(frozen=True, slots=True)
class VideoStill:
    """Where to take the frame of a video, and with which `ffmpeg`."""

    path: Path
    moment: float  # seconds from the start
    landscape: bool  # shown wider than tall: the width is shrunk to the edge
    ffmpeg: str


def still_of(path: Path, metadata: MediaMetadata, ffmpeg: str) -> VideoStill | None:
    """Plan the frame of a video, from what the probe read.

    Args:
        path: The video.
        metadata: Its length, size and rotation.
        ffmpeg: Path of the `ffmpeg` executable.

    Returns:
        The frame to take, or None without a length or a size.
    """
    duration, width, height = metadata.duration, metadata.width, metadata.height
    if not duration or not width or not height:
        return None
    if (metadata.rotation or 0) % _FULL_TURN in _QUARTER_TURNS:
        width, height = height, width
    return VideoStill(path, duration * MIDDLE, width >= height, ffmpeg)


def shown_size(metadata: MediaMetadata) -> int:
    """The shorter side of a video, in pixels: the model is not shown thumbnails.

    Args:
        metadata: Its size, as the probe read it.

    Returns:
        The shorter side; 0 when unknown.
    """
    return min(metadata.width or 0, metadata.height or 0)


async def video_jpeg(still: VideoStill, edge: int) -> bytes | None:
    """Decode the frame and make a JPEG of it.

    Args:
        still: The video, the moment, its orientation and `ffmpeg`.
        edge: The longer side of the JPEG, in pixels.

    Returns:
        The JPEG, or None when the frame cannot be decoded.
    """
    scale = f"scale={edge}:-2" if still.landscape else f"scale=-2:{edge}"
    command = (
        still.ffmpeg,
        *_BEFORE_INPUT,
        *("-ss", f"{still.moment:.3f}", "-i", str(still.path)),
        *_AFTER_INPUT,
        *("-vf", scale),
        *_OUTPUT,
    )
    run = await run_tool(command, _TIMEOUT_SECONDS)
    row = edge * _CHANNELS
    if run is None or run.returncode != 0 or not run.stdout or len(run.stdout) % row:
        _LOGGER.debug("No still of %s at %.3f s", still.path, still.moment)
        return None
    other = len(run.stdout) // row
    size = (edge, other) if still.landscape else (other, edge)
    picture = Image.frombytes("RGB", size, run.stdout)
    buffer = io.BytesIO()
    picture.save(buffer, "JPEG", quality=_JPEG_QUALITY)
    return buffer.getvalue()
