"""Describe the photos missing from the cache, a few at a time, stopping on request.

Each photo is made a JPEG of `image_edge` pixels in the process pool (a RAW file gives
its embedded preview; a video, one frame `ffmpeg` decodes), sent, and its description
committed at once. Ctrl+C lets the
photos being described finish; the next run starts where this one stopped. The
question asked is `classify`'s unless another one is given (`tags` asks its own).
"""

from __future__ import annotations

import asyncio
import time
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.ai.prompts import describe_request, read_description
from media_hygiene.errors import AiError
from media_hygiene.report.thumbnails import jpeg_preview
from media_hygiene.scan.video_still import video_jpeg

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping, Sequence
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.classify.ai.client import OllamaClient
    from media_hygiene.classify.ai.models import Description
    from media_hygiene.index.descriptions import DescriptionStore, PhotoVersion
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.scan.video_still import VideoStill


@dataclass(frozen=True, slots=True)
class Question:
    """How a photo is asked about (model, JPEG → body), and how its answer is read."""

    request: Callable[[str, bytes], dict[str, object]]
    read: Callable[[str, float], Description | None]


CLASSIFY_QUESTION: Final = Question(describe_request, read_description)


@dataclass(frozen=True, slots=True)
class DescribeDeps:
    """What describing needs: the model, the cache, the pool, the progress, Ctrl+C."""

    client: OllamaClient
    store: DescriptionStore
    executor: Executor
    progress: ProgressSink
    stopped: Callable[[], bool]
    question: Question = CLASSIFY_QUESTION
    # The videos among the photos, and the frame each one is seen by.
    stills: Mapping[Path, VideoStill] = field(
        default_factory=lambda: MappingProxyType({})
    )


@dataclass(slots=True)
class DescribeOutcome:
    """How a describing run went."""

    described: int = 0  # videos included
    videos: int = 0  # among the described: videos, seen by one frame
    unreadable: int = 0  # undecodable photos, or answers outside the schema
    stopped: bool = False
    errors: list[AiError] = field(default_factory=list)


async def describe_all(
    photos: Sequence[PhotoVersion], deps: DescribeDeps
) -> DescribeOutcome:
    """Describe photos, `concurrency` at a time.

    Args:
        photos: The photos missing from the cache.
        deps: Model, cache, pool, progress and Ctrl+C.

    Returns:
        How many were described; the first model error, if any, is in `errors`.
    """
    outcome = DescribeOutcome()
    gate = asyncio.Semaphore(deps.client.settings.concurrency)
    async with asyncio.TaskGroup() as group:
        tasks = [
            group.create_task(_describe_one(photo, deps, (gate, outcome)))
            for photo in photos
        ]
    del tasks  # all awaited by the group
    return outcome


async def _describe_one(
    photo: PhotoVersion,
    deps: DescribeDeps,
    run: tuple[asyncio.Semaphore, DescribeOutcome],
) -> None:
    """Describe one photo, unless the run must stop.

    Args:
        photo: The photo.
        deps: Model, cache, pool, progress and Ctrl+C.
        run: The concurrency gate and the outcome to update.
    """
    gate, outcome = run
    async with gate:
        if outcome.errors:
            return
        if deps.stopped():
            outcome.stopped = True
            return
        settings = deps.client.settings
        image = await _picture(photo.path, deps)
        if image is None:
            outcome.unreadable += 1
            deps.progress.advance()
            return
        started = time.monotonic()
        try:
            content = await deps.client.chat(
                deps.question.request(settings.model, image)
            )
        except AiError as exc:
            outcome.errors.append(exc)
            return
        description = deps.question.read(content, time.monotonic() - started)
        if description is None:
            outcome.unreadable += 1
        else:
            deps.store.put(photo, description)
            outcome.described += 1
            outcome.videos += photo.path in deps.stills
        deps.progress.advance()


async def _picture(path: Path, deps: DescribeDeps) -> bytes | None:
    """The JPEG the model sees: the photo, or the frame of a video.

    Args:
        path: The photo or video.
        deps: The pool, the size of the JPEG, the frames of the videos.

    Returns:
        The JPEG, or None when it cannot be decoded.
    """
    edge = deps.client.settings.image_edge
    still = deps.stills.get(path)
    if still is not None:
        return await video_jpeg(still, edge)
    loop = asyncio.get_running_loop()
    return await loop.run_in_executor(deps.executor, jpeg_preview, path, edge)
