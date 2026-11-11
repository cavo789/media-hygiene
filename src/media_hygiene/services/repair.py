"""`clean --repair`: restore the damaged files from their good copy (0690).

Refused without a persistent journal or on read-only photo folders, like every change
of this tool. Each restored file is read again from the disk once its run ends: only
those proven are counted restored, and the index forgets their damage.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.repair import RepairExecutor, RepairJob
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.verified_rows import Reading, note_good
from media_hygiene.scan.hashing import full_digest
from media_hygiene.services.acting import ensure_can_act
from media_hygiene.services.journaled_run import new_run
from media_hygiene.services.reread import today

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.scan.progress import ProgressSink
    from media_hygiene.services.good_copy import Repairable
    from media_hygiene.services.runtime import Runtime


@dataclass(frozen=True, slots=True)
class RepairResult:
    """What a run did: its identifier, its outcome, the files proven restored."""

    run_id: str
    outcome: Outcome
    proven: tuple[Path, ...]


def jobs_of(found: Sequence[Repairable]) -> list[RepairJob]:
    """The restorations possible: the damaged files with a good copy.

    Args:
        found: The damaged files.

    Returns:
        One job each that has a copy.
    """
    return [
        RepairJob(
            Path(item.damaged.path),
            (item.damaged.size, item.damaged.mtime_ns),
            item.copy,
            item.damaged.digest,
        )
        for item in found
        if item.copy is not None
    ]


def repair(
    runtime: Runtime, jobs: Sequence[RepairJob], progress: ProgressSink
) -> RepairResult:
    """Restore each file under a new run, then read each one back.

    Args:
        runtime: Settings, mount points and output.
        jobs: The restorations, as shown to the user.
        progress: Where to report progress.

    Returns:
        What was done.
    """
    ensure_can_act(runtime, Phase.CLEAN.value)
    tally = Tally()
    with new_run(runtime, progress, Phase.CLEAN) as context:
        executor = RepairExecutor(context, tally)
        executor.run(jobs, _never)
    by_target = {job.target: job for job in jobs}
    proven = tuple(
        path for path in executor.restored if _read_back(path, by_target[path].digest)
    )
    index = runtime.index_file
    if index is not None and index.is_file():
        with FactsRepository.open(index) as repository:
            for path in proven:
                job = by_target[path]
                reading = Reading(str(path), job.stat, job.digest, today())
                note_good(repository.connection, reading)
    return RepairResult(context.quarantine_run_dir.name, tally.freeze(), proven)


def _read_back(path: Path, digest: str) -> bool:
    """Read a restored file from the disk.

    Args:
        path: The file.
        digest: The good SHA-256.

    Returns:
        True when it holds it.
    """
    try:
        return full_digest(path) == digest
    except OSError:
        return False


def _never() -> bool:
    """A run of a few files is not stopped between two (no Ctrl+C handler).

    Returns:
        False.
    """
    return False
