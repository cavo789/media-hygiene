"""`tags` run by the home page, in a worker thread: the cheap words, then the model.

`prepare` writes the folder, name, date and place words (seconds) and measures what
the vision model would still describe; the page shows those figures and asks.
`describe` sends the photos, for a time or until Stop: each answer is committed at
once, so a stop (or the end of the home server) keeps what is described and the next
run goes on (`services/tag_describe.py`). Only the cache is written: photos stay
read-only.
"""

from __future__ import annotations

import logging
import threading
import time
from typing import TYPE_CHECKING

from media_hygiene.console.page_progress import AuditStoppedError, PageProgress
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.services.home_tags_models import (
    PageTags,
    TagsPhase,
    TagsRunner,
)

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)
_SECONDS_PER_MINUTE = 60


class HomeTags:
    """Starts each half in a thread, one at a time, tells its progress, stops it."""

    __slots__ = (
        "_clock",
        "_end",
        "_lock",
        "_progress",
        "_run",
        "_stop",
        "_thread",
    )

    def __init__(self, run: TagsRunner) -> None:
        """Prepare, without starting.

        Args:
            run: The cheap half and the model's half.
        """
        self._run = run
        self._lock = threading.Lock()
        self._progress: PageProgress | None = None
        self._thread: threading.Thread | None = None
        self._end = PageTags()
        self._stop = threading.Event()
        self._clock: tuple[float, float | None] = (0.0, None)  # since, deadline

    def prepare(self) -> bool:
        """Write the cheap words and count the photos to describe.

        Returns:
            False when a half already runs.
        """
        return self._launch(TagsPhase.PREPARING, self._prepare)

    def describe(self, minutes: int | None) -> bool:
        """Send the photos the cache lacks to the model.

        Args:
            minutes: Stop by itself after that long; None: until done or Stop.

        Returns:
            False when a half already runs, or nothing was prepared.
        """
        with self._lock:
            if self._end.figures is None:
                return False
            now = time.monotonic()
            deadline = None if minutes is None else now + minutes * _SECONDS_PER_MINUTE
            self._clock = (now, deadline)
        return self._launch(TagsPhase.RUNNING, self._describe)

    def stop(self) -> None:
        """Stop after the photo in flight, and wait until it has."""
        self._stop.set()
        with self._lock:
            progress, thread = self._progress, self._thread
        if progress is not None and self._end.phase is TagsPhase.PREPARING:
            progress.request_stop()
        if thread is not None:
            thread.join()

    def state(self) -> PageTags:
        """What the page shows.

        Returns:
            The state, with the steps so far.
        """
        with self._lock:
            progress, end = self._progress, self._end
            since = self._clock[0]
        update: dict[str, object] = {}
        if end.phase is TagsPhase.RUNNING:
            update["elapsed"] = time.monotonic() - since
        if progress is not None:
            update["steps"], update["current"] = progress.snapshot()
        return end.model_copy(update=update)

    def _launch(self, phase: TagsPhase, work: Callable[[PageProgress], None]) -> bool:
        """Start a half in a thread, unless one runs.

        Args:
            phase: The phase while it runs.
            work: The half.

        Returns:
            False when a half already runs.
        """
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._stop.clear()
            self._progress = PageProgress()
            figures = self._end.figures if phase is TagsPhase.RUNNING else None
            self._end = PageTags(phase=phase, figures=figures)
            self._thread = threading.Thread(
                target=self._guarded, args=(work, self._progress), name="home-tags"
            )
            self._thread.start()
            return True

    def _prepare(self, progress: PageProgress) -> None:
        """The cheap half; then the page asks.

        Args:
            progress: Where it reports.
        """
        figures = self._run.prepare(progress)
        self._finish(PageTags(phase=TagsPhase.ASKING, figures=figures))

    def _describe(self, progress: PageProgress) -> None:
        """The model's half.

        Args:
            progress: Where it reports.
        """
        lines = self._run.describe(progress, self._stopped)
        phase = TagsPhase.STOPPED if self._stop.is_set() else TagsPhase.DONE
        self._finish(PageTags(phase=phase, lines=lines))

    def _stopped(self) -> bool:
        """Tell whether to stop before the next photo: Stop, or the time is up.

        Returns:
            True to stop.
        """
        deadline = self._clock[1]
        return self._stop.is_set() or (
            deadline is not None and time.monotonic() >= deadline
        )

    def _guarded(
        self, work: Callable[[PageProgress], None], progress: PageProgress
    ) -> None:
        """Run a half; any failure becomes one line on the page, never a traceback.

        Args:
            work: The half.
            progress: Where it reports.
        """
        try:
            work(progress)
        except* AuditStoppedError:
            self._finish(PageTags(phase=TagsPhase.STOPPED))
        except* MediaHygieneError as group:
            first = group.exceptions[0]
            message = first.message if isinstance(first, MediaHygieneError) else ""
            self._finish(PageTags(phase=TagsPhase.FAILED, error=message))
        # Any bug: the page says it failed in one line, the terminal logs it.
        except* Exception:  # pylint: disable=broad-exception-caught
            _LOGGER.exception("a step started from the home page failed")
            self._finish(
                PageTags(
                    phase=TagsPhase.FAILED,
                    error=_("It failed: the window where mh runs says why."),
                )
            )
        progress.stop()

    def _finish(self, end: PageTags) -> None:
        """Record how a half ended.

        Args:
            end: The state the page shows then.
        """
        with self._lock:
            self._end = end
