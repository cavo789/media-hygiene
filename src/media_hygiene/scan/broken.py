"""Find broken files (empty, undecodable, unopenable) and describe readable ones.

A file the disk or the cloud could not read this time is neither broken nor stored:
it is listed (`unread`) and read again at the next audit (`read_errors`).
"""

from __future__ import annotations

from dataclasses import dataclass, field
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import BrokenReason, MediaKind
from media_hygiene.scan.bounded import bounded_map, pool_in_flight
from media_hygiene.scan.check_steps import check_step, metadata_step
from media_hygiene.scan.file_check import FileChecker, Need, need_of
from media_hygiene.scan.first_checks import FirstChecks, Pace
from media_hygiene.scan.models import BrokenFile
from media_hygiene.scan.partial_fill import fill_partials
from media_hygiene.scan.read_errors import ReadFailedError, UnreadFile
from media_hygiene.scan.video_prints import VideoPrinter

if TYPE_CHECKING:
    from collections.abc import Callable, Coroutine, Mapping, Sequence
    from pathlib import Path

    from media_hygiene.index.facts import FileFacts
    from media_hygiene.scan.deps import IntegrityTools, ScanDeps
    from media_hygiene.scan.metadata import MediaMetadata
    from media_hygiene.scan.models import MediaFile, VisualFacts
    from media_hygiene.scan.progress import Step
    from media_hygiene.scan.video_models import VideoLook

    type _Action = Callable[[MediaFile], Coroutine[None, None, FileFacts]]

# Other files (asked for with --ext) are never checked: nothing says what they hold.
_MEDIA_KINDS: Final = frozenset({MediaKind.IMAGE, MediaKind.RAW, MediaKind.VIDEO})
_EMPTY_DETAIL = "0 bytes"


@dataclass(frozen=True, slots=True)
class IntegrityFindings:
    """Broken files, what readable images and videos look like, what files say.

    `unread`: the files the disk or the cloud could not read this time, by path.
    """

    broken: tuple[BrokenFile, ...]
    visuals: Mapping[Path, VisualFacts]
    metadata: Mapping[Path, MediaMetadata] = field(
        default_factory=lambda: MappingProxyType({})
    )
    videos: Mapping[Path, VideoLook] = field(
        default_factory=lambda: MappingProxyType({})
    )
    unread: tuple[UnreadFile, ...] = ()


@dataclass(frozen=True, slots=True)
class _Pass:
    """One pass over files: what it does to each, and what the user sees."""

    action: _Action
    step: Step
    timed: bool = False


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
        self._unread: list[UnreadFile] = []

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
        self._unread = []
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
        if known and not work[Need.CHECK] and not work[Need.METADATA]:
            self._deps.reporter.nothing_new(len(known))
        checks = _Pass(self._checker.check, check_step(), timed=True)
        known |= await self._run(work[Need.CHECK], checks)
        reading = _Pass(self._checker.read_metadata, metadata_step())
        known |= await self._run(work[Need.METADATA], reading)
        known |= await fill_partials(files, known, self._deps)
        videos = await self._printer.looks(files, known)
        by_path = {file.path: file for file in files}
        broken.extend(
            BrokenFile(by_path[path], facts.broken_reason, facts.broken_detail)
            for path, facts in known.items()
            if facts.broken_reason is not None
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
            unread=tuple(sorted(self._unread, key=lambda item: str(item.file.path))),
        )

    async def _run(self, files: list[MediaFile], run: _Pass) -> dict[Path, FileFacts]:
        """Run one action on every file concurrently, storing each file as it ends.

        Stored at once, not after the pass: the index commits every few seconds, so a
        run killed halfway keeps the files already checked (TODO 0143). A file that
        could not be read is listed in `_unread`, never stored.

        Args:
            files: The files needing it.
            run: The action, its progress step (nothing shown for no file), and
                whether its pace is told (the first checks only).

        Returns:
            The updated facts, by path.
        """
        if not files:
            return {}
        repository = self._deps.repository
        tell = self._deps.reporter.first_checks if run.timed else _untold
        pace = Pace(FirstChecks.of(files), tell)

        async def stored(file: MediaFile) -> FileFacts | None:
            """Run the action on one file, then store its facts.

            Args:
                file: The file.

            Returns:
                Its updated facts; None when it could not be read.
            """
            try:
                facts = await run.action(file)
            except ReadFailedError as failure:
                self._unread.append(UnreadFile(file, failure.detail))
                pace.one_done()
                return None
            repository.put(file, facts)
            pace.one_done()
            return facts

        self._deps.progress.start(run.step, len(files))
        done = await bounded_map(files, stored, pool_in_flight())
        self._deps.progress.stop()
        return {
            file.path: facts
            for file, facts in zip(files, done, strict=True)
            if facts is not None
        }


def _untold(_checks: FirstChecks) -> None:
    """Say nothing of a pass whose pace does not matter."""
