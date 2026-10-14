"""How long each stage of an audit took, so users see where the time goes."""

from __future__ import annotations

import time
from contextlib import contextmanager
from dataclasses import dataclass
from enum import StrEnum
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Iterator


class Stage(StrEnum):
    """The stages of an audit, in the order they run."""

    LISTING = "listing"
    INDEX = "index"
    INTEGRITY = "integrity"
    DIGESTS = "digests"
    SIMILAR = "similar"
    COLOURS = "colours"
    STREAMS = "streams"


@dataclass(frozen=True, slots=True)
class StageTime:
    """The time one stage took, every run of it added up."""

    stage: Stage
    seconds: float


class Stopwatch:
    """Adds up the time spent in each stage; a stage run twice counts twice."""

    def __init__(self) -> None:
        """Start with no stage timed."""
        self._totals: dict[Stage, float] = {}

    @contextmanager
    def timing(self, stage: Stage) -> Iterator[None]:
        """Time the block, even when it raises.

        Args:
            stage: What the block does.

        Yields:
            Nothing: the time is recorded when the block ends.
        """
        started = time.monotonic()
        try:
            yield
        finally:
            elapsed = time.monotonic() - started
            self._totals[stage] = self._totals.get(stage, 0.0) + elapsed

    def times(self) -> tuple[StageTime, ...]:
        """Every stage timed, in the order stages run.

        Returns:
            The durations; a stage that did not run is left out.
        """
        return tuple(
            StageTime(stage, self._totals[stage])
            for stage in Stage
            if stage in self._totals
        )
