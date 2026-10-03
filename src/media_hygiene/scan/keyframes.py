"""Hash a few frames of a video with `ffmpeg`: the fingerprint of re-encoded copies.

`ffmpeg` decodes one frame at each of `FRAME_POSITIONS` (an accurate seek: the frame
shown at that moment, whatever the keyframes of the encoding), turned upright, shrunk
to a small grayscale square. The hashes are those of images (`visual`). One process
per frame, on one thread: the scan runs several videos at once instead.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from PIL import Image

from media_hygiene.scan.tool_run import run_tool
from media_hygiene.scan.video_models import FRAME_POSITIONS, FrameHash, VideoPrint
from media_hygiene.scan.visual import dhash, phash

if TYPE_CHECKING:
    from pathlib import Path

_LOGGER = logging.getLogger(__name__)
FRAME_EDGE: Final = 64
_FRAME_BYTES: Final = FRAME_EDGE * FRAME_EDGE
_TIMEOUT_SECONDS: Final = 60
_FILTER: Final = f"scale={FRAME_EDGE}:{FRAME_EDGE}:flags=area,format=gray"
_BEFORE_INPUT: Final = ("-nostdin", "-v", "error", "-threads", "1")
_AFTER_INPUT: Final = (
    *("-map", "0:v:0", "-frames:v", "1", "-an", "-sn", "-dn"),
    *("-filter_threads", "1", "-vf", _FILTER, "-f", "rawvideo", "pipe:1"),
)


async def fingerprint(path: Path, duration: float, ffmpeg: str) -> VideoPrint | None:
    """Hash the frames of a video at `FRAME_POSITIONS`.

    Args:
        path: Video file.
        duration: Its length in seconds, as the probe read it.
        ffmpeg: Path of the `ffmpeg` executable.

    Returns:
        The fingerprint, or None when a frame cannot be decoded (a codec the
        executable lacks, a damaged stream, a timeout).
    """
    frames: list[FrameHash] = []
    for position in FRAME_POSITIONS:
        frame = await _frame(path, duration * position, ffmpeg)
        if frame is None:
            return None
        frames.append(frame)
    return VideoPrint(tuple(frames))


def frame_hash(pixels: bytes) -> FrameHash:
    """Hash one frame.

    Args:
        pixels: `FRAME_EDGE` x `FRAME_EDGE` grayscale pixels, row by row.

    Returns:
        Its hashes.
    """
    gray = Image.frombytes("L", (FRAME_EDGE, FRAME_EDGE), pixels)
    return FrameHash(dhash(gray), phash(gray))


async def _frame(path: Path, seconds: float, ffmpeg: str) -> FrameHash | None:
    """Decode the frame shown at a moment and hash it.

    Args:
        path: Video file.
        seconds: The moment.
        ffmpeg: Path of the `ffmpeg` executable.

    Returns:
        Its hashes, or None when it cannot be decoded.
    """
    command = (
        ffmpeg,
        *_BEFORE_INPUT,
        *("-ss", f"{seconds:.3f}", "-i", str(path)),
        *_AFTER_INPUT,
    )
    run = await run_tool(command, _TIMEOUT_SECONDS)
    if run is None:
        _LOGGER.warning("ffmpeg timed out on %s at %.3f s", path, seconds)
        return None
    if run.returncode != 0 or len(run.stdout) != _FRAME_BYTES:
        _LOGGER.info(
            "No frame of %s at %.3f s: %s",
            path,
            seconds,
            run.stderr.decode(errors="replace").strip() or f"{len(run.stdout)} bytes",
        )
        return None
    return frame_hash(run.stdout)
