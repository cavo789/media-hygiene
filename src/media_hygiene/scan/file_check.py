"""Check one file, or only read its metadata when the index knows the rest.

Images are decoded by Pillow and RAW files by LibRaw in the worker pool; videos are
opened by `ffprobe`. Each check also records what the file says about itself. An image
an older version indexed only gets its header read again: no decode.
"""

from __future__ import annotations

import asyncio
from enum import Enum, auto
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.scan.image_check import inspect_image, read_image_metadata
from media_hygiene.scan.metadata import METADATA_VERSION
from media_hygiene.scan.raw_check import inspect_raw
from media_hygiene.scan.video_check import probe_video

if TYPE_CHECKING:
    from collections.abc import Callable, Mapping
    from pathlib import Path

    from media_hygiene.index.facts import FileFacts
    from media_hygiene.scan.deps import IntegrityTools, ScanDeps
    from media_hygiene.scan.image_check import ImageInspection
    from media_hygiene.scan.models import MediaFile

_REASONS: Final[Mapping[MediaKind, BrokenReason]] = MappingProxyType(
    {
        MediaKind.IMAGE: BrokenReason.UNREADABLE_IMAGE,
        MediaKind.RAW: BrokenReason.UNREADABLE_RAW,
        MediaKind.VIDEO: BrokenReason.UNREADABLE_VIDEO,
    }
)


class Need(Enum):
    """What remains to learn about a file the index may already know."""

    NOTHING = auto()
    CHECK = auto()
    METADATA = auto()


def need_of(file: MediaFile, facts: FileFacts) -> Need:
    """Tell what a check would still compute for this file.

    Images checked by an older version still lack their visual facts: they are decoded
    again once. Readable images and videos indexed before their metadata was recorded
    get it once: from the header for images, from the usual probe for videos.

    Args:
        file: The file.
        facts: What the index knows about it.

    Returns:
        Nothing, a full check, or the metadata only.
    """
    if not facts.integrity_checked:
        return Need.CHECK
    if file.kind is MediaKind.IMAGE and not facts.visual_checked:
        return Need.CHECK
    if facts.broken_reason is not None or file.kind is MediaKind.RAW:
        return Need.NOTHING  # a broken file has nothing more to tell
    if facts.metadata_version == METADATA_VERSION:
        return Need.NOTHING
    return Need.METADATA if file.kind is MediaKind.IMAGE else Need.CHECK


class FileChecker:
    """Checks one file at a time; the finder runs many of them concurrently."""

    def __init__(self, deps: ScanDeps, tools: IntegrityTools) -> None:
        """Keep the shared collaborators and the checking tools.

        Args:
            deps: Index, progress sink and I/O concurrency limit.
            tools: Image-decoding pool and optional `ffprobe`.
        """
        self._deps = deps
        self._tools = tools

    def can_check(self, file: MediaFile) -> bool:
        """Tell whether a decoder exists for this file.

        Args:
            file: Candidate file.

        Returns:
            True for images and RAW files, and for videos when `ffprobe` is available.
        """
        if file.kind is MediaKind.VIDEO:
            return self._tools.ffprobe is not None
        return file.kind in {MediaKind.IMAGE, MediaKind.RAW}

    async def check(self, file: MediaFile) -> FileFacts:
        """Check one file and return its updated facts.

        Args:
            file: File to check.

        Returns:
            Its facts, including the integrity outcome and its metadata.
        """
        facts = self._deps.repository.get(file)
        try:
            if file.kind is MediaKind.VIDEO and self._tools.ffprobe is not None:
                async with self._deps.io_slots:
                    probe = await probe_video(file.path, self._tools.ffprobe)
                problem = probe.problem
                facts = facts.with_metadata(probe.metadata)
            else:
                inspection = await self._in_pool(_decoder(file.kind), file.path)
                problem = inspection.problem
                facts = facts.with_visual(inspection.visual)
                if file.kind is MediaKind.IMAGE:
                    facts = facts.with_metadata(inspection.metadata)
        finally:
            self._deps.progress.advance()
        return facts.with_integrity(
            _REASONS[file.kind] if problem else None, problem or ""
        )

    async def read_metadata(self, file: MediaFile) -> FileFacts:
        """Read only the metadata of an image the index knows, from its header.

        Args:
            file: An image already checked by an older version.

        Returns:
            Its facts, the metadata added.
        """
        facts = self._deps.repository.get(file)
        try:
            metadata = await self._in_pool(read_image_metadata, file.path)
        finally:
            self._deps.progress.advance()
        return facts.with_metadata(metadata)

    async def _in_pool[T](self, work: Callable[[Path], T], path: Path) -> T:
        """Run a function of the file in the worker pool.

        Args:
            work: A picklable function of a path.
            path: The file.

        Returns:
            What the function returned.
        """
        loop = asyncio.get_running_loop()
        return await loop.run_in_executor(self._tools.executor, work, path)


def _decoder(kind: MediaKind) -> Callable[[Path], ImageInspection]:
    """Choose how to decode an image or a RAW file (looked up at call time).

    Args:
        kind: IMAGE or RAW.

    Returns:
        The inspection function.
    """
    return inspect_image if kind is MediaKind.IMAGE else inspect_raw
