"""The progress contract the scan reports to, decoupled from Rich."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Protocol


@dataclass(frozen=True, slots=True)
class Step:
    """A long step as the user sees it: a short title and what it really does.

    `total_weight` (bytes, typically) makes the bar and its estimate follow the work
    rather than the count: copying a 2 GB video first is not 1/12,000 of the job.
    """

    title: str
    hint: str = ""
    total_weight: int | None = None


class ProgressSink(Protocol):
    """Receives progress updates of a long step."""

    def start(self, step: Step, total: int | None) -> None:
        """Begin a step.

        Args:
            step: Translated title and explanation of the step.
            total: Number of units of work, or None when unknown in advance (the
                step then shows a running count instead of a bar).
        """

    def advance(self, weight: int = 1) -> None:
        """Mark one unit of work as done.

        Args:
            weight: Its share of `Step.total_weight` (ignored without one).
        """

    def current(self, text: str) -> None:
        """Say what is being done right now, on one line under the bar.

        Args:
            text: Translated, e.g. the action and the file it is about.
        """

    def stop(self) -> None:
        """End the current step."""


class NullProgress:
    """A progress sink that shows nothing (tests, non-interactive runs)."""

    def start(self, step: Step, total: int | None) -> None:
        """Ignore the start of a step.

        Args:
            step: Unused.
            total: Unused.
        """

    def advance(self, weight: int = 1) -> None:
        """Ignore progress.

        Args:
            weight: Unused.
        """

    def current(self, text: str) -> None:
        """Ignore what is being done.

        Args:
            text: Unused.
        """

    def stop(self) -> None:
        """Ignore the end of a step."""
