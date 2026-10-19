"""The audit the home page runs itself, in a worker thread, one at a time.

The audit only reads the photos: it runs in the home page's own container, its
photos mounted read-only. Its progress goes to a `PageProgress` the page polls; the
end of the home server stops it between two files, the index keeping what it
committed.
"""

from __future__ import annotations

import logging
import threading
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.console.page_progress import (
    AuditPhase,
    AuditStoppedError,
    PageAudit,
    PageProgress,
)
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Callable

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class AuditResult:
    """What the page shows once the audit is over."""

    lines: tuple[str, ...]
    actions: tuple[str, ...] = ()
    report: str | None = None  # its address on the page
    timed: str | None = None  # `Time per step: …`, as the console says it (0241)


class HomeAudit:
    """Starts the audit in a thread, tells its progress, stops it."""

    __slots__ = ("_end", "_lock", "_progress", "_run", "_thread")

    def __init__(self, run: Callable[[PageProgress], AuditResult]) -> None:
        """Prepare, without starting.

        Args:
            run: Audits and writes the report, reporting to the progress given.
        """
        self._run = run
        self._lock = threading.Lock()
        self._progress: PageProgress | None = None
        self._thread: threading.Thread | None = None
        self._end = PageAudit()

    def start(self) -> bool:
        """Start the audit, unless one runs.

        Returns:
            False when an audit already runs.
        """
        with self._lock:
            if self._thread is not None and self._thread.is_alive():
                return False
            self._progress = PageProgress()
            self._end = PageAudit(phase=AuditPhase.RUNNING)
            self._thread = threading.Thread(
                target=self._work, args=(self._progress,), name="home-audit"
            )
            self._thread.start()
            return True

    def stop(self) -> None:
        """Ask the audit to stop between two files, and wait until it has."""
        with self._lock:
            progress = self._progress
        if progress is not None:
            progress.request_stop()
        self.wait()

    def wait(self) -> None:
        """Wait until the audit running, if any, has ended."""
        with self._lock:
            thread = self._thread
        if thread is not None:
            thread.join()

    def state(self) -> PageAudit:
        """What the page shows: the steps so far, then the summary.

        Returns:
            The state.
        """
        with self._lock:
            progress, end = self._progress, self._end
        if progress is None:
            return end
        steps, current = progress.snapshot()
        return end.model_copy(update={"steps": steps, "current": current})

    def _work(self, progress: PageProgress) -> None:
        """Run the audit, then record how it ended.

        Args:
            progress: Where the audit reports.
        """
        try:
            result = self._run(progress)
        except* AuditStoppedError:
            end = PageAudit(
                phase=AuditPhase.STOPPED,
                error=_("Audit stopped: the cache keeps what it had read."),
            )
        except* MediaHygieneError as group:
            first = group.exceptions[0]
            message = first.message if isinstance(first, MediaHygieneError) else ""
            end = PageAudit(phase=AuditPhase.FAILED, error=message)
        # Any bug: the page says it failed in one line, the terminal logs it.
        except* Exception:  # pylint: disable=broad-exception-caught
            _LOGGER.exception("The audit started from the home page failed")
            end = PageAudit(
                phase=AuditPhase.FAILED,
                error=_("The audit failed: the window where mh runs says why."),
            )
        else:
            end = PageAudit(
                phase=AuditPhase.DONE,
                lines=result.lines,
                actions=result.actions,
                report=result.report,
                timed=result.timed,
            )
        progress.stop()
        with self._lock:
            self._end = end
