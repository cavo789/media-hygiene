"""Fingerprint the readable videos once per version, and describe them for comparison.

Runs after the integrity check, which already read the length and the size of each
video. A video the index fingerprinted with the current version is not decoded again;
without `ffmpeg`, only the fingerprints already in the index are used.
"""

from __future__ import annotations

import asyncio
import os
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MediaKind
from media_hygiene.i18n import _
from media_hygiene.scan.keyframes import fingerprint
from media_hygiene.scan.progress import Step
from media_hygiene.scan.video_models import VIDEO_PRINT_VERSION, VideoLook

if TYPE_CHECKING:
    from collections.abc import Mapping, Sequence
    from pathlib import Path

    from media_hygiene.index.facts import FileFacts
    from media_hygiene.scan.deps import ScanDeps
    from media_hygiene.scan.models import MediaFile

# Shorter clips hold too few distinct frames to tell two of them apart.
MIN_DURATION: Final = 1.0
_QUARTER_TURNS: Final = frozenset({90, 270})
_FULL_TURN: Final = 360


class VideoPrinter:
    """Fingerprints videos with `ffmpeg`, several at once, one thread each."""

    def __init__(self, deps: ScanDeps, ffmpeg: str | None) -> None:
        """Keep the index, the progress sink and the executable.

        Args:
            deps: Index and progress sink.
            ffmpeg: Path of the `ffmpeg` executable, None when it is unavailable.
        """
        self._deps = deps
        self._ffmpeg = ffmpeg
        self._slots = asyncio.Semaphore(os.process_cpu_count() or 1)

    async def looks(
        self, files: Sequence[MediaFile], known: Mapping[Path, FileFacts]
    ) -> dict[Path, VideoLook]:
        """Fingerprint the videos that need it, then describe every fingerprinted one.

        Args:
            files: Every media file found.
            known: The facts of the files checked, healthy or broken.

        Returns:
            What each fingerprinted video looks like, by path.
        """
        videos = [file for file in files if _comparable(known.get(file.path), file)]
        facts = {file.path: known[file.path] for file in videos}
        missing = [
            file
            for file in videos
            if facts[file.path].video_print_version != VIDEO_PRINT_VERSION
        ]
        if self._ffmpeg is not None and missing:
            facts |= await self._fingerprint(missing, facts, self._ffmpeg)
        return {
            path: look
            for path, item in facts.items()
            if (look := look_of(item)) is not None
        }

    async def _fingerprint(
        self, files: list[MediaFile], facts: Mapping[Path, FileFacts], ffmpeg: str
    ) -> dict[Path, FileFacts]:
        """Fingerprint videos concurrently, then store the fingerprints.

        Args:
            files: The videos to fingerprint.
            facts: Their current facts.
            ffmpeg: Path of the `ffmpeg` executable.

        Returns:
            Their updated facts, by path.
        """
        progress = self._deps.progress
        progress.start(_fingerprint_step(), len(files))

        async def one(file: MediaFile) -> FileFacts:
            """Fingerprint one video, one slot at a time.

            Args:
                file: The video.

            Returns:
                Its facts, the fingerprint added (None when not decodable).
            """
            current = facts[file.path]
            duration = current.metadata.duration if current.metadata else None
            async with self._slots:
                found = await fingerprint(file.path, duration or 0.0, ffmpeg)
            progress.advance()
            return current.with_video_print(found)

        async with asyncio.TaskGroup() as group:
            tasks = {file: group.create_task(one(file)) for file in files}
        progress.stop()
        for file, task in tasks.items():
            self._deps.repository.put(file, task.result())
        return {file.path: task.result() for file, task in tasks.items()}


def look_of(facts: FileFacts) -> VideoLook | None:
    """Describe a fingerprinted video for comparison.

    Args:
        facts: Its facts.

    Returns:
        Its look, or None without a fingerprint, a length or a size.
    """
    metadata = facts.metadata
    if facts.video_print is None or metadata is None:
        return None
    if not metadata.duration or not metadata.width or not metadata.height:
        return None
    width, height = metadata.width, metadata.height
    if (metadata.rotation or 0) % _FULL_TURN in _QUARTER_TURNS:
        width, height = height, width
    return VideoLook(
        print=facts.video_print,
        duration=metadata.duration,
        width=width,
        height=height,
        recorded_at=metadata.recorded_at,
        codec=metadata.codec,
    )


def _comparable(facts: FileFacts | None, file: MediaFile) -> bool:
    """Tell whether a file is a healthy video long enough to fingerprint.

    Args:
        facts: Its facts, None when it was not checked.
        file: The file.

    Returns:
        True for a readable video of at least `MIN_DURATION` seconds.
    """
    if file.kind is not MediaKind.VIDEO or facts is None or facts.metadata is None:
        return False
    duration = facts.metadata.duration
    return facts.broken_reason is None and (duration or 0.0) >= MIN_DURATION


def _fingerprint_step() -> Step:
    """The progress step of fingerprinting videos.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Fingerprinting videos"),
        _(
            "Once per video: a few frames are decoded and hashed, to find the same "
            "video saved again (re-encoded, resized). The cache keeps the result."
        ),
    )
