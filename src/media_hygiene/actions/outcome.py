"""Results of `clean` and `undo`: what was done, skipped or failed — and why."""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class Incident:
    """A file left untouched, with the translated reason."""

    path: Path
    reason: str


@dataclass(slots=True)
class Tally:
    """Mutable counters filled while acting, frozen into an outcome at the end."""

    done: int = 0
    bytes_done: int = 0
    quarantined: int = 0
    skipped: list[Incident] = field(default_factory=list[Incident])
    failed: list[Incident] = field(default_factory=list[Incident])
    started: float = field(default_factory=time.monotonic)

    def freeze(self) -> Outcome:
        """Snapshot the counters.

        Returns:
            The immutable outcome.
        """
        return Outcome(
            done=self.done,
            bytes_done=self.bytes_done,
            quarantined=self.quarantined,
            skipped=tuple(self.skipped),
            failed=tuple(self.failed),
            seconds=time.monotonic() - self.started,
        )


@dataclass(frozen=True, slots=True)
class Outcome:
    """Final counts of a `clean` or `undo` run."""

    done: int
    bytes_done: int
    quarantined: int
    skipped: tuple[Incident, ...]
    failed: tuple[Incident, ...]
    seconds: float = 0.0


def combine(outcomes: Sequence[Outcome]) -> Outcome:
    """Sum the outcomes of several runs acted on together (a sort undone whole).

    Args:
        outcomes: The outcome of each run.

    Returns:
        One outcome: counts and durations summed, incidents of every run.
    """
    return Outcome(
        done=sum(outcome.done for outcome in outcomes),
        bytes_done=sum(outcome.bytes_done for outcome in outcomes),
        quarantined=sum(outcome.quarantined for outcome in outcomes),
        skipped=tuple(item for outcome in outcomes for item in outcome.skipped),
        failed=tuple(item for outcome in outcomes for item in outcome.failed),
        seconds=sum(outcome.seconds for outcome in outcomes),
    )
