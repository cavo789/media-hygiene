"""The loop of a run acting on one file at a time: progress, Ctrl+C, failures counted.

Shared by the runs that write files one by one (`xmp`'s sidecars, `import`'s copies): a
file that fails is counted with its reason and the run goes on; Ctrl+C stops it between
two files.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.outcome import Incident, why

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence
    from pathlib import Path

    from media_hygiene.actions.outcome import Tally
    from media_hygiene.scan.progress import ProgressSink, Step

_LOGGER = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class JobLoop[J]:
    """How a run acts on each job, and where it counts and reports."""

    progress: ProgressSink
    step: Step
    tally: Tally
    act: Callable[[J], None]
    path_of: Callable[[J], Path]  # the file a failure is told about

    def run(self, jobs: Sequence[J], stop: Callable[[], bool]) -> bool:
        """Act on every job; a failure is counted and the run goes on.

        Args:
            jobs: The jobs, in order.
            stop: Tells when Ctrl+C was pressed: the run stops between two jobs.

        Returns:
            True when Ctrl+C stopped the run.
        """
        self.progress.start(self.step, len(jobs))
        stopped = False
        for job in jobs:
            if stop():
                stopped = True
                break
            try:
                self.act(job)
            # A file that cannot be read or written, or holds what cannot be parsed
            # (an XmpError is a ValueError): counted, the run goes on.
            except (OSError, ValueError) as exc:
                _LOGGER.debug("Not done: %s", self.path_of(job), exc_info=True)
                self.tally.failed.append(Incident(self.path_of(job), why(exc)))
            self.progress.advance()
        self.progress.stop()
        return stopped
