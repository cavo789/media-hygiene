"""Find broken files (empty, undecodable, unopenable) and describe readable ones."""

from __future__ import annotations

import asyncio
from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.i18n import _
from media_hygiene.scan.file_check import FileChecker, Need, need_of
from media_hygiene.scan.models import BrokenFile
from media_hygiene.scan.progress import Step
from media_hygiene.scan.video_prints import VideoPrinter

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.index.facts import FileFacts
    from media_hygiene.scan.deps import IntegrityTools, ScanDeps
    from media_hygiene.scan.metadata import MediaMetadata
    from media_hygiene.scan.models import MediaFile, VisualFacts
    from media_hygiene.scan.video_models import VideoLook

    type _Action = Callable[[MediaFile], Coroutine[None, None, FileFacts]]

# Other files (asked for with --ext) are never checked: nothing says what they hold.
_MEDIA_KINDS: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW, MediaKind.VIDEO})
_EMPTY_DETAIL = "0 bytes"


@dataclass(frozen=True, slots=True)
class IntegrityFindings:
    """Broken files, what readable images and videos look like, what files say."""

    broken: tuple[BrokenFile, ...]
    visuals: Mapping[Path, VisualFacts]
    metadata: Mapping[Path, MediaMetadata] = field(
        default_factory=lambda: MappingProxyType({})
    )
    videos: Mapping[Path, VideoLook] = field(
        default_factory=lambda: MappingProxyType({})
    )


class BrokenFileFinder:
    """Checks every file once per version; results are cached in the index."""

    def __init__(self, deps: ScanDeps, tools: IntegrityTools) -> None:
        """Keep the shared collaborators and the checking tools.

        Args:
            deps: Index, progress sink and I/O concurrency limit.
            tools: Image-decoding pool and optional `ffprobe` and `ffmpeg`.
        """
        self._deps = deps
        self._checker = FileChecker(deps, tools)
        self._printer = VideoPrinter(deps, tools.ffmpeg)

    async def find(self, files: Sequence[MediaFile]) -> IntegrityFindings:
        """Return the broken files among `files`, and describe the readable ones.

        Images are decoded by Pillow, RAW files by LibRaw, videos opened by `ffprobe`
        (skipped when it is unavailable). Other files are never broken, even empty:
        an empty file can be a marker a program needs.

        Args:
            files: Every media file found.

        Returns:
            The broken files, sorted by path, the visual facts of images, the
            metadata of images and videos, and the fingerprints of videos.
        """
        broken = [
            BrokenFile(file, BrokenReason.EMPTY, _EMPTY_DETAIL)
            for file in files
            if file.size == 0 and file.kind in _MEDIA_KINDS
        ]
        work: dict[Need, list[MediaFile]] = {need: [] for need in Need}
        known: dict[Path, FileFacts] = {}
        for file in files:
            if file.size == 0 or not self._checker.can_check(file):
                continue
            facts = self._deps.repository.get(file)
            need = need_of(file, facts)
            work[need].append(file)
            if need is Need.NOTHING:
                known[file.path] = facts
        known |= await self._run(work[Need.CHECK], self._checker.check, _check_step())
        known |= await self._run(
            work[Need.METADATA], self._checker.read_metadata, _metadata_step()
        )
        videos = await self._printer.looks(files, known)
        by_path = {file.path: file for file in files}
        broken.extend(
            item
            for path, facts in known.items()
            for item in _as_broken(by_path[path], facts)
        )
        return IntegrityFindings(
            broken=tuple(sorted(broken, key=lambda item: str(item.file.path))),
            visuals=MappingProxyType(
                {path: facts.visual for path, facts in known.items() if facts.visual}
            ),
            metadata=MappingProxyType(
                {
                    path: facts.metadata
                    for path, facts in known.items()
                    if facts.metadata
                }
            ),
            videos=MappingProxyType(videos),
        )

    async def _run(
        self, files: list[MediaFile], action: _Action, step: Step
    ) -> dict[Path, FileFacts]:
        """Run one action on every file concurrently, then store what it learnt.

        Args:
            files: The files needing it.
            action: A full check, or reading the metadata only.
            step: The progress step shown meanwhile (nothing shown for no file).

        Returns:
            The updated facts, by path.
        """
        if not files:
            return {}
        self._deps.progress.start(step, len(files))
        async with asyncio.TaskGroup() as group:
            tasks = {file: group.create_task(action(file)) for file in files}
        self._deps.progress.stop()
        for file, task in tasks.items():
            self._deps.repository.put(file, task.result())
        return {file.path: task.result() for file, task in tasks.items()}


def _check_step() -> Step:
    """The progress step of the full checks.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Checking that files can be read"),
        _(
            "Finds broken files: empty (0 bytes), images and RAW files that cannot "
            "be decoded, videos that cannot be opened."
        ),
    )


def _metadata_step() -> Step:
    """The progress step of the one-time metadata reading, after an update.

    Returns:
        Its translated title and explanation.
    """
    return Step(
        _("Reading the metadata of files already in the cache"),
        _(
            "Once, after an update: dates, places and devices recorded in the files. "
            "Images are not decoded again, only their header is read."
        ),
    )


def _as_broken(file: MediaFile, facts: FileFacts) -> list[BrokenFile]:
    """Turn cached facts into a broken-file record when they say so.

    Args:
        file: The file.
        facts: Its integrity facts.

    Returns:
        One record when broken, none otherwise.
    """
    if facts.broken_reason is None:
        return []
    return [BrokenFile(file, facts.broken_reason, facts.broken_detail)]
