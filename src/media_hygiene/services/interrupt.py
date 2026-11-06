"""Turn Ctrl+C into a request to stop between two files, instead of in the middle."""

from __future__ import annotations

import signal
import threading
from concurrent.futures.process import BrokenProcessPool
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
    from collections.abc import Callable
    from types import FrameType


class StopRequest:
    """While active, Ctrl+C asks the run to stop; the run asks `requested()`."""

    def __init__(self) -> None:
        """Start with no request."""
        self._requested = False
        self._previous: object = None

    def __enter__(self) -> Self:
        """Catch Ctrl+C (only the main thread may).

        Returns:
            The request itself.
        """
        if threading.current_thread() is threading.main_thread():
            self._previous = signal.signal(signal.SIGINT, self._handle)
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Give Ctrl+C its usual meaning back.

        Args:
            *exc_info: Exception details from the `with` statement (unused).
        """
        if self._previous is not None:
            signal.signal(signal.SIGINT, self._previous)  # type: ignore[arg-type]

    def _handle(self, _signal: int, _frame: FrameType | None) -> None:
        """Record the request; the current file finishes first.

        Args:
            _signal: The signal (SIGINT).
            _frame: The interrupted frame.
        """
        self._requested = True

    def requested(self) -> bool:
        """Tell whether Ctrl+C was pressed.

        Returns:
            True once it was.
        """
        return self._requested


def broken_by_stop(error: BaseException, stopped: Callable[[], bool]) -> bool:
    """Tell whether a broken process pool is the doing of a Ctrl+C.

    Ctrl+C reaches every process of the terminal: when a stop was asked, a pool that
    lost a process (alone or inside a task group) is a stop, not a bug (0627).

    Args:
        error: What ended the run.
        stopped: Whether the user asked to stop.

    Returns:
        True when the pool broke after a stop request.
    """
    if not stopped():
        return False
    if isinstance(error, BaseExceptionGroup):
        return error.subgroup(BrokenProcessPool) is not None
    return isinstance(error, BrokenProcessPool)
