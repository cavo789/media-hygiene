"""Find the faces of a video: a few frames of it, analysed like photos (TODO 0839).

`ffmpeg` decodes the frame shown at each of `FACE_MOMENTS` (upright, its longer side
`FACE_EDGE` pixels: the face boxes are in that frame's pixels, and `face_frame` cuts
a face out of the same frame again). The faces of every frame are found as a photo's,
then one person seen on several frames is kept once: two faces of different frames
whose vectors are as close as two faces of one person (`SFACE_SIMILARITY`) are one,
the sharper one stays, with the moment of its frame.

Measured on 20 real videos (2026-11-27, 4 CPUs, 9 frames): 0.1 to 1.6 s of decoding
and 0.1 to 0.4 s of detection per video; every video with someone in it showed them
on most frames, so five frames keep the people and halve the cost.
"""

from __future__ import annotations

import asyncio
import shutil
import time
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

import numpy as np

from media_hygiene.constants import FFMPEG_BINARY, FFPROBE_BINARY
from media_hygiene.faces.models import PhotoFaces, vector_of
from media_hygiene.faces.similarity import SFACE_SIMILARITY
from media_hygiene.faces.turn_guess import NO_TURN
from media_hygiene.faces.worker import finder_of
from media_hygiene.scan.video_check import probe_video
from media_hygiene.scan.video_still import VideoStill, still_of, video_picture

if TYPE_CHECKING:
    from pathlib import Path

    from PIL import Image

    from media_hygiene.faces.models import Face
    from media_hygiene.faces.worker import FaceJob

FACE_MOMENTS: Final = (0.1, 0.3, 0.5, 0.7, 0.9)  # shares of the length
FACE_EDGE: Final = 1280  # the longer side of the frames analysed, in pixels


@dataclass(frozen=True, slots=True)
class VideoFaces:
    """The faces of a video, and the moment (seconds) of the frame of each."""

    found: PhotoFaces
    moments: tuple[float, ...]


@dataclass(frozen=True, slots=True)
class _Seen:
    """A face of one frame: which frame, when."""

    face: Face
    frame: int
    moment: float


def find_video_faces(job: FaceJob) -> VideoFaces | None:
    """Find the faces of a video on a few of its frames, one person kept once.

    Runs in a worker process, like `find_faces`.

    Args:
        job: The video and the recipe.

    Returns:
        Its faces and their moments; None without `ffmpeg`, or when no frame
        can be decoded.
    """
    ffmpeg, ffprobe = shutil.which(FFMPEG_BINARY), shutil.which(FFPROBE_BINARY)
    if ffmpeg is None or ffprobe is None:
        return None
    started = time.monotonic()
    plan = asyncio.run(_plan(job.path, (ffprobe, ffmpeg)))
    if plan is None:
        return None
    finder = finder_of(job.recipe)
    seen: list[_Seen] = []
    decoded = 0
    for frame, share in enumerate(FACE_MOMENTS):
        moment = plan.moment * share
        picture = asyncio.run(_picture(plan, moment))
        if picture is None:
            continue
        decoded += 1
        seen.extend(_Seen(face, frame, moment) for face in finder.find(picture))
    if not decoded:
        return None
    kept = once_each(seen)
    found = PhotoFaces(
        job.path,
        job.size,
        job.mtime_ns,
        tuple(one.face for one in kept),
        time.monotonic() - started,
        NO_TURN,
    )
    return VideoFaces(found, tuple(one.moment for one in kept))


def once_each(seen: list[_Seen]) -> list[_Seen]:
    """Keep one face per person: the sharpest of those alike on other frames.

    Args:
        seen: The faces of every frame, frame by frame.

    Returns:
        The faces kept, in the order first seen.
    """
    kept: list[_Seen] = []
    for one in seen:
        vector = vector_of(one.face.embedding)
        twin = next(
            (
                index
                for index, other in enumerate(kept)
                if other.frame != one.frame
                and float(np.dot(vector, vector_of(other.face.embedding)))
                >= SFACE_SIMILARITY
            ),
            None,
        )
        if twin is None:
            kept.append(one)
        elif one.face.sharpness > kept[twin].face.sharpness:
            kept[twin] = one
    return kept


def frame_picture(path: Path, moment: float) -> Image.Image | None:
    """Decode a video's frame again, as it was analysed: to cut a face out of it.

    Args:
        path: The video.
        moment: Seconds from the start (`index.face_frames`).

    Returns:
        The frame, or None without `ffmpeg` or when it cannot be decoded.
    """
    ffmpeg, ffprobe = shutil.which(FFMPEG_BINARY), shutil.which(FFPROBE_BINARY)
    if ffmpeg is None or ffprobe is None:
        return None
    plan = asyncio.run(_plan(path, (ffprobe, ffmpeg)))
    return None if plan is None else asyncio.run(_picture(plan, moment))


async def _plan(path: Path, tools: tuple[str, str]) -> VideoStill | None:
    """Probe a video: its length and orientation.

    Args:
        path: The video.
        tools: `ffprobe` and `ffmpeg`.

    Returns:
        Its still at the middle (`moment` is half its length), or None.
    """
    probe = await probe_video(path, tools[0])
    if probe.metadata is None:
        return None
    still = still_of(path, probe.metadata, tools[1])
    if still is None:
        return None
    return VideoStill(still.path, still.moment * 2, still.landscape, still.ffmpeg)


async def _picture(plan: VideoStill, moment: float) -> Image.Image | None:
    """Decode the frame at a moment, at `FACE_EDGE`.

    Args:
        plan: The video (its length as `moment`).
        moment: Seconds from the start.

    Returns:
        The frame, or None.
    """
    still = VideoStill(plan.path, moment, plan.landscape, plan.ffmpeg)
    return await video_picture(still, FACE_EDGE)
