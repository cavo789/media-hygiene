"""Find the faces of the photos the index lacks, a few at a time, stopping on request.

Each photo is decoded and analysed in the process pool, and its faces committed at
once: Ctrl+C lets the photos under way finish, and the next run starts where this one
stopped. Half the CPUs work at most: each worker holds both models in memory.
"""

from __future__ import annotations

import asyncio
import os
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.faces.worker import FaceJob, find_faces
from media_hygiene.i18n import ngettext

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from concurrent.futures import Executor

    from media_hygiene.faces.models import PhotoFaces
    from media_hygiene.faces.worker import FinderRecipe
    from media_hygiene.index.descriptions import PhotoVersion
    from media_hygiene.index.face_rows import FaceStore
    from media_hygiene.scan.progress import ProgressSink

_SHARE: Final = 2  # one worker per this many CPUs


@dataclass(frozen=True, slots=True)
class FindDeps:
    """What finding needs: the recipe, the store, the pool, progress, Ctrl+C."""

    recipe: FinderRecipe
    store: FaceStore
    executor: Executor
    progress: ProgressSink
    stopped: Callable[[], bool]


@dataclass(slots=True)
class FindOutcome:
    """How a run went: photos analysed, faces found, undecodable photos, Ctrl+C."""

    seconds: float = 0.0  # summed over the photos analysed, decoding included
    analysed: int = 0
    faces: int = 0
    unreadable: int = 0
    stopped: bool = False

    def estimate(self, photos: int) -> float:
        """How long analysing more photos should take, at the pace of this run.

        Args:
            photos: How many more.

        Returns:
            Seconds, `workers()` photos at a time; 0 before any photo was analysed.
        """
        if not self.analysed:
            return 0.0
        return self.seconds / self.analysed * photos / workers()


def workers() -> int:
    """How many photos are analysed at once.

    Returns:
        Half the CPUs this process may use, at least one.
    """
    return max(1, (os.process_cpu_count() or 1) // _SHARE)


async def find_all(photos: Sequence[PhotoVersion], deps: FindDeps) -> FindOutcome:
    """Analyse photos, `workers()` at a time.

    Args:
        photos: The photos missing from the index.
        deps: Recipe, store, pool, progress and Ctrl+C.

    Returns:
        How it went.
    """
    run = _Run(deps)
    async with asyncio.TaskGroup() as group:
        started = [group.create_task(run.analyse(photo)) for photo in photos]
    del started  # all awaited by the group
    return run.outcome


class _Run:
    """One run: its gate, what it needs, and how it goes so far."""

    def __init__(self, deps: FindDeps) -> None:
        """Start a run.

        Args:
            deps: Recipe, store, pool, progress and Ctrl+C.
        """
        self.deps = deps
        self.outcome = FindOutcome()
        self._gate = asyncio.Semaphore(workers())

    async def analyse(self, photo: PhotoVersion) -> None:
        """Analyse one photo in the pool and keep its faces, unless the run stops.

        Args:
            photo: The photo.
        """
        async with self._gate:
            if self.deps.stopped():
                self.outcome.stopped = True
                return
            job = FaceJob(photo.path, photo.size, photo.mtime_ns, self.deps.recipe)
            loop = asyncio.get_running_loop()
            found = await loop.run_in_executor(self.deps.executor, find_faces, job)
            self._count(found)
            self.deps.progress.advance()

    def _count(self, found: PhotoFaces | None) -> None:
        """Keep the faces of a photo, and count it.

        Args:
            found: Its faces; None when it could not be decoded.
        """
        if found is None:
            self.outcome.unreadable += 1
            return
        self.deps.store.put(found)
        self.outcome.analysed += 1
        self.outcome.faces += len(found.faces)
        count = len(found.faces)
        self.deps.progress.current(
            ngettext(
                "Last photo: {count} face", "Last photo: {count} faces", count
            ).format(count=count)
        )
        self.outcome.seconds += found.seconds
