"""How colourful a picture or a video is: a black and white version is not a copy.

Perceptual hashes are computed in grey: a black and white edit of a colour photo
hashes like its original. The colourfulness of Hasler and Süsstrunk (2003) tells them
apart: about 0 for black and white, 15 for a dull picture, 33 and more for an ordinary
colour one. It is measured only for the pictures and videos already found alike, on a
small square, and kept in the index (`index.measures`) for the next audits.
"""

from __future__ import annotations

import asyncio
import logging
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np
from PIL import Image, UnidentifiedImageError

from media_hygiene.i18n import _
from media_hygiene.scan.progress import Step
from media_hygiene.scan.tool_run import run_tool

if TYPE_CHECKING:
    from collections.abc import Collection, Mapping
    from concurrent.futures import Executor
    from pathlib import Path

    from numpy.typing import NDArray

    from media_hygiene.scan.progress import ProgressSink

_LOGGER = logging.getLogger(__name__)
_EDGE: Final = 64
_RGB_BYTES: Final = _EDGE * _EDGE * 3
_MEAN_WEIGHT: Final = 0.3
_HALF: Final = 0.5
# Moments of the video frames measured, as shares of the length.
_VIDEO_POSITIONS: Final = (0.3, 0.5, 0.7)
_TIMEOUT_SECONDS: Final = 60
_FFMPEG_OPTIONS: Final = ("-nostdin", "-v", "error", "-threads", "1")
_FRAME_OUTPUT: Final = (
    *("-map", "0:v:0", "-frames:v", "1", "-an", "-sn", "-dn"),
    *("-vf", f"scale={_EDGE}:{_EDGE}:flags=area", "-pix_fmt", "rgb24"),
    *("-f", "rawvideo", "pipe:1"),
)


def colourfulness(rgb: NDArray[np.uint8]) -> float:
    """The colourfulness of Hasler and Süsstrunk.

    Args:
        rgb: Pixels, height x width x 3.

    Returns:
        About 0 for black and white, 33 and more for an ordinary colour picture.
    """
    red, green, blue = (rgb[..., channel].astype(np.float64) for channel in range(3))
    red_green = red - green
    yellow_blue = _HALF * (red + green) - blue
    spread = np.hypot(red_green.std(), yellow_blue.std())
    mean = np.hypot(red_green.mean(), yellow_blue.mean())
    return float(spread + _MEAN_WEIGHT * mean)


def image_colour(path: Path) -> float | None:
    """Measure a photo, decoded at a reduced scale when the format allows it.

    Args:
        path: The photo.

    Returns:
        Its colourfulness, None when it cannot be decoded.
    """
    try:
        with Image.open(path) as image:
            image.draft("RGB", (_EDGE, _EDGE))
            small = image.convert("RGB").resize((_EDGE, _EDGE))
    except OSError, UnidentifiedImageError, Image.DecompressionBombError:
        return None
    return colourfulness(np.asarray(small, dtype=np.uint8))


async def video_colour(path: Path, duration: float, ffmpeg: str) -> float | None:
    """Measure a video: the mean over a few frames.

    Args:
        path: The video.
        duration: Its length in seconds.
        ffmpeg: Path of the `ffmpeg` executable.

    Returns:
        Its colourfulness, None when no frame can be decoded.
    """
    found: list[float] = []
    for position in _VIDEO_POSITIONS:
        command = (
            ffmpeg,
            *_FFMPEG_OPTIONS,
            *("-ss", f"{duration * position:.3f}", "-i", str(path)),
            *_FRAME_OUTPUT,
        )
        run = await run_tool(command, _TIMEOUT_SECONDS)
        if run is None or run.returncode != 0 or len(run.stdout) != _RGB_BYTES:
            _LOGGER.debug("No colour frame of %s at %.0f %%", path, position * 100)
            continue
        pixels = np.frombuffer(run.stdout, dtype=np.uint8).reshape(_EDGE, _EDGE, 3)
        found.append(colourfulness(pixels))
    return sum(found) / len(found) if found else None


@dataclass(frozen=True, slots=True)
class ColourTools:
    """What measuring needs: `ffmpeg`, where to report progress, a pool for the photos.

    The pool is one of processes outside the tests: decoding holds the GIL.
    """

    ffmpeg: str | None
    progress: ProgressSink
    executor: Executor


async def colours(
    images: Collection[Path], videos: Mapping[Path, float], tools: ColourTools
) -> dict[Path, float]:
    """Measure photos (in the pool) and videos (one `ffmpeg` each), several at once.

    Args:
        images: The photos.
        videos: The videos and their lengths; left out without `ffmpeg`.
        tools: `ffmpeg`, the progress sink and the pool.

    Returns:
        The colourfulness of each picture or video measured, by path.
    """
    slots = asyncio.Semaphore(os.process_cpu_count() or 1)
    ffmpeg, progress = tools.ffmpeg, tools.progress
    loop = asyncio.get_running_loop()
    measured = dict(videos) if ffmpeg is not None else {}

    async def one(path: Path) -> float | None:
        """Measure one picture or video, one slot at a time.

        Args:
            path: The picture or video.

        Returns:
            Its colourfulness, None when it cannot be decoded.
        """
        async with slots:
            if path in measured and ffmpeg is not None:
                value = await video_colour(path, measured[path], ffmpeg)
            else:
                value = await loop.run_in_executor(tools.executor, image_colour, path)
        progress.advance()
        return value

    progress.start(_colour_step(), len(images) + len(measured))
    async with asyncio.TaskGroup() as group:
        tasks = {path: group.create_task(one(path)) for path in (*images, *measured)}
    progress.stop()
    return {
        path: value
        for path, task in tasks.items()
        if (value := task.result()) is not None
    }


def _colour_step() -> Step:
    """The progress step of measuring colours.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Comparing colours"),
        _(
            "Only for the pictures and videos found alike: a black and white edit "
            "of a colour picture is not a copy of it."
        ),
    )
