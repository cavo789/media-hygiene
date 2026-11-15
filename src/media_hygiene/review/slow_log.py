"""Say in the window where a slow answer of a page spent its time.

A request over `SLOW_SECONDS` is logged as a warning, with its laps when the
handler kept some: the maintainer reads where the seconds went without a profiler
(2026-11-15: names confirmed on /person took about 10 s each).
"""

from __future__ import annotations

import logging
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final

if TYPE_CHECKING:
    from collections.abc import Awaitable

SLOW_SECONDS: Final = 1.0
_LOGGER: Final = logging.getLogger(__name__)


@dataclass(slots=True)
class Laps:
    """The time of each step of one answer, in the order they ran."""

    what: str
    started: float = field(default_factory=time.perf_counter)
    last: float = 0.0
    steps: list[tuple[str, float]] = field(default_factory=list)

    def lap(self, step: str) -> None:
        """Close a step: the time since the previous one.

        Args:
            step: Its name.
        """
        now = time.perf_counter()
        self.steps.append((step, now - (self.last or self.started)))
        self.last = now

    def said(self) -> None:
        """Log the laps when the whole answer was slow."""
        total = time.perf_counter() - self.started
        if total < SLOW_SECONDS:
            return
        parts = " · ".join(f"{step} {seconds:.2f} s" for step, seconds in self.steps)
        _LOGGER.warning("Slow: %s took %.2f s (%s)", self.what, total, parts)


async def timed[T](what: str, answer: Awaitable[T]) -> T:
    """Await an answer; log it when it was slow.

    Args:
        what: The request, e.g. `POST /person/api/names`.
        answer: Its handler at work.

    Returns:
        What the handler returned.
    """
    laps = Laps(what)
    try:
        return await answer
    finally:
        laps.said()
