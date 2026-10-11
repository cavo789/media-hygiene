"""A new journaled run: its identifier, its journal, its quarantine folder.

`album` and `xmp` start their runs alike; the identifier names the journal file and
the run's folder in the quarantine (`context.quarantine_run_dir.name`).
"""

from __future__ import annotations

from contextlib import contextmanager
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalWriter, journal_file
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.runs import new_run_id

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.actions.kinds import Phase
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.runtime import Runtime


@contextmanager
def new_run(
    runtime: Runtime, progress: ProgressSink, phase: Phase
) -> Iterator[CleanContext]:
    """Open the journal of a new run.

    Args:
        runtime: Settings, mount points and output.
        progress: Where the run reports progress.
        phase: The command acting.

    Yields:
        Where and how the run acts; its identifier is `quarantine_run_dir.name`.
    """
    locations = runtime.locations
    locations.journal_dir.mkdir(parents=True, exist_ok=True)
    run_id = new_run_id(locations.journal_dir)
    with JournalWriter.open(journal_file(locations.journal_dir, run_id)) as journal:
        yield CleanContext(
            journal,
            runtime.mapper,
            locations.quarantine_dir / run_id,
            progress,
            phase,
        )
