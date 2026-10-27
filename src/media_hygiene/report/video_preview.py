"""A video's preview: one frame, early in it, as the photos' previews (TODO 0373).

Runs in a worker process, as `jpeg_preview`: `ffprobe` reads the video's length,
size and rotation, `ffmpeg` decodes the frame at a tenth of its length (past a
black first frame, before the subject leaves), each with its time limit.
"""

from __future__ import annotations

import asyncio
import dataclasses
import shutil
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import FFMPEG_BINARY, FFPROBE_BINARY
from media_hygiene.scan.video_check import probe_video
from media_hygiene.scan.video_still import MIDDLE, still_of, video_jpeg

if TYPE_CHECKING:
    from pathlib import Path

# The moment shown, as a share of the length.
_MOMENT: Final = 0.1


def video_preview(source: Path, edge: int) -> bytes | None:
    """Render a frame of a video as an upright JPEG, its longer side `edge` pixels.

    Args:
        source: The video.
        edge: The longer side, in pixels.

    Returns:
        The JPEG bytes, or None without `ffmpeg` or for a video that cannot be read.
    """
    ffmpeg, ffprobe = shutil.which(FFMPEG_BINARY), shutil.which(FFPROBE_BINARY)
    if ffmpeg is None or ffprobe is None:
        return None
    return asyncio.run(_frame(source, edge, (ffprobe, ffmpeg)))


async def _frame(source: Path, edge: int, tools: tuple[str, str]) -> bytes | None:
    """Probe the video, then decode its frame.

    Args:
        source: The video.
        edge: The longer side, in pixels.
        tools: `ffprobe` and `ffmpeg`.

    Returns:
        The JPEG bytes, or None.
    """
    probe = await probe_video(source, tools[0])
    if probe.metadata is None:
        return None
    still = still_of(source, probe.metadata, tools[1])
    if still is None:
        return None
    moment = still.moment / MIDDLE * _MOMENT  # `still_of` plans the middle
    return await video_jpeg(dataclasses.replace(still, moment=moment), edge)
