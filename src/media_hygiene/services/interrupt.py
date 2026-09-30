"""Turn Ctrl+C into a request to stop between two files, instead of in the middle."""

from __future__ import annotations

import signal
import threading
from typing import TYPE_CHECKING, Self

if TYPE_CHECKING:
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
