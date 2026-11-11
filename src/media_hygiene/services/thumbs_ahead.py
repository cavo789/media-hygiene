"""The grid's thumbnails made at the end of an audit, so the library opens fast (0674).

The audit is written first: this step only fills `/cache/previews`, the very files the
library page would render at first display (same function, same name). Thumbnails
already kept cost a `stat`; Ctrl+C stops between two files and loses nothing, the
rest being made when a page shows them. Without a persistent cache, nothing to do.
"""

from __future__ import annotations

from concurrent.futures import FIRST_COMPLETED, wait
from concurrent.futures.process import BrokenProcessPool
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.report.preview_ahead import made_ahead
from media_hygiene.report.preview_cache import PreviewJob
from media_hygiene.report.thumbnails import PREVIEWABLE
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.progress import Step
from media_hygiene.search.thumbs import GRID_EDGE
from media_hygiene.services.interrupt import broken_by_stop

if TYPE_CHECKING:
    from collections.abc import Callable, Iterable
    from concurrent.futures import Executor, Future
    from pathlib import Path

    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime

# Jobs handed to the pool at once, per worker: enough to keep it busy, few enough
# that Ctrl+C stops in about a second.
_IN_FLIGHT_PER_WORKER: Final = 2


@dataclass(frozen=True, slots=True)
class AheadRun:
    """Where the thumbnails go, how the user is shown it, and whether to stop."""

    progress: ProgressSink
    stopped: Callable[[], bool]


@dataclass(frozen=True, slots=True)
class AheadOutcome:
    """How many thumbnails were made, how many files were left for the pages."""

    made: int
    left: int


def pictures(paths: Iterable[Path]) -> list[Path]:
    """The files a thumbnail is made for: photos and RAW files, in a stable order.

    Args:
        paths: Every media path the audit listed.

    Returns:
        The pictures, sorted (a stop then resumes where it left off, next audit).
    """
    return sorted(path for path in paths if media_kind(path) in PREVIEWABLE)


def make_thumbnails(
    runtime: Runtime, paths: list[Path], run: AheadRun
) -> AheadOutcome | None:
    """Make the grid thumbnails missing from the cache, in the worker pool.

    Args:
        runtime: The cache folder and the pool.
        paths: The pictures (`pictures`).
        run: Progress and Ctrl+C.

    Returns:
        How it went, or None without a persistent cache.

    Raises:
        BrokenProcessPool: The pool broke without a stop request.
    """
    folder = runtime.previews_dir
    if folder is None or not paths:
        return None
    run.progress.start(
        Step(
            _("Thumbnails of the library"),
            _(
                "Ctrl+C skips this step at any time: the audit is saved, the rest is "
                "made when a page shows it."
            ),
        ),
        len(paths),
    )
    jobs = [PreviewJob(path, GRID_EDGE, folder) for path in paths]
    with runtime.executor_factory() as executor:
        try:
            made, done = _fill(executor, jobs, run)
        except BrokenProcessPool as error:
            if not broken_by_stop(error, run.stopped):
                raise
            made, done = 0, 0  # stopped: the count of this run is lost, not its files
        finally:
            run.progress.stop()
    return AheadOutcome(made, len(jobs) - done)


def _fill(executor: Executor, jobs: list[PreviewJob], run: AheadRun) -> tuple[int, int]:
    """Run the jobs a few at a time until all are done or a stop is asked.

    Args:
        executor: The worker pool.
        jobs: One per picture.
        run: Progress and Ctrl+C.

    Returns:
        The thumbnails decoded, the jobs finished.
    """
    width = _IN_FLIGHT_PER_WORKER * max(1, getattr(executor, "_max_workers", 1))
    queue = iter(jobs)
    running: set[Future[bool]] = set()
    made = done = 0
    while True:
        while len(running) < width and not run.stopped():
            job = next(queue, None)
            if job is None:
                break
            running.add(executor.submit(made_ahead, job))
        if not running:
            return made, done
        finished, running = wait(running, return_when=FIRST_COMPLETED)
        for future in finished:
            made += future.result()
            done += 1
            run.progress.advance()
