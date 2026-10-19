"""A progress sink for a page, next to the Rich one: the steps kept for a JSON endpoint.

The audit started from the home page runs in a worker thread and reports here; the
page polls what was recorded. A stop asked by the page (or the end of the server) is
raised at the next report, between two files: the index keeps what it committed, as
on Ctrl+C.
"""

from __future__ import annotations

import threading
from enum import StrEnum
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict

if TYPE_CHECKING:
    from media_hygiene.scan.progress import Step


class AuditStoppedError(Exception):
    """The page asked the audit to stop: raised at its next progress report."""


class AuditPhase(StrEnum):
    """Where the audit started from the page stands."""

    IDLE = "idle"
    RUNNING = "running"
    DONE = "done"
    STOPPED = "stopped"
    FAILED = "failed"


class PageStep(BaseModel):
    """One step of the audit, as `Time per step` names it, with its counts."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    title: str
    hint: str = ""
    total: int | None = None  # None: a running count
    done: int = 0
    finished: bool = False


class PageAudit(BaseModel):
    """What the page shows of the audit: its steps, then its summary."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    phase: AuditPhase = AuditPhase.IDLE
    steps: tuple[PageStep, ...] = ()
    current: str = ""
    lines: tuple[str, ...] = ()  # the summary, once done
    actions: tuple[str, ...] = ()  # what you can do, once done
    report: str | None = None  # the report's address on the page
    timed: str | None = None  # `Time per step: …`, once done (0241)
    error: str | None = None


class PageProgress:
    """Records the steps reported by a worker thread; read by the page's server."""

    __slots__ = ("_current", "_lock", "_steps", "_stopping")

    def __init__(self) -> None:
        """Start with no step."""
        self._lock = threading.Lock()
        self._steps: list[PageStep] = []
        self._current = ""
        self._stopping = threading.Event()

    def start(self, step: Step, total: int | None) -> None:
        """Begin a step; the previous one is finished.

        Args:
            step: Translated title and explanation of the step.
            total: Number of units of work, or None when unknown in advance.
        """
        self._check()
        with self._lock:
            self._finish()
            self._steps.append(PageStep(title=step.title, hint=step.hint, total=total))
            self._current = ""

    def advance(self, weight: int = 1) -> None:
        """Count one unit of work of the current step.

        Args:
            weight: Its share of the step's weight (the page counts units).
        """
        del weight  # counted, not weighed
        self._check()
        with self._lock:
            if self._steps:
                last = self._steps[-1]
                self._steps[-1] = last.model_copy(update={"done": last.done + 1})

    def current(self, text: str) -> None:
        """Say what is being done right now.

        Args:
            text: Translated, e.g. the action and the file it is about.
        """
        self._check()
        with self._lock:
            self._current = text

    def stop(self) -> None:
        """End the current step."""
        with self._lock:
            self._finish()
            self._current = ""

    def request_stop(self) -> None:
        """Ask the work to stop at its next report."""
        self._stopping.set()

    def snapshot(self) -> tuple[tuple[PageStep, ...], str]:
        """The steps so far and what is being done.

        Returns:
            The steps, in order, and the current line.
        """
        with self._lock:
            return tuple(self._steps), self._current

    def _check(self) -> None:
        """Stop the work when asked to.

        Raises:
            AuditStoppedError: The page asked for it.
        """
        if self._stopping.is_set():
            raise AuditStoppedError

    def _finish(self) -> None:
        """Mark the last step finished (the lock held)."""
        if self._steps and not self._steps[-1].finished:
            self._steps[-1] = self._steps[-1].model_copy(update={"finished": True})
