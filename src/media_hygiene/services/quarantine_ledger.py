"""What a run's quarantine holds, from its journal instead of a walk of the disk (0277).

Through Docker Desktop each `stat` of a Windows drive costs about 3 ms: the census of
a quarantine of 18,506 files took 55-61 s at each home page shown, 97 % of it
(measured on the maintainer's PC, `mh-measure.ps1` step 23, 2026-10-20). The journal
already records each file set aside with its size, and undo the ones it put back
(the same `seq`). Only runs whose folder is still in a quarantine are asked about (the
listing of its top level, one per drive): a purged run, or its folder removed by
hand, is gone. A file deleted by hand inside a run's folder still counts until
`purge`; `purge` itself walks the disk. A run whose journal cannot be read is walked.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, journal_file, read_journal
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.runs import run_phase
from media_hygiene.errors import JournalError

if TYPE_CHECKING:
    from pathlib import Path


def journal_census(journal_dir: Path, run_id: str) -> tuple[int, int] | None:
    """Count the files a run set aside and undo did not put back, and their size.

    Args:
        journal_dir: Journal mount point.
        run_id: The run, whose folder is still in a quarantine.

    Returns:
        How many files, and their size in bytes; None when its journal is missing
        or unreadable (the caller then walks the folder).
    """
    try:
        entries = read_journal(journal_file(journal_dir, run_id))
    except JournalError, OSError:
        return None
    put_back = {entry.seq for entry in done_states(entries, Phase.UNDO)}
    held = [
        entry
        for entry in done_states(entries, run_phase(entries))
        if entry.action in QUARANTINED and entry.seq not in put_back
    ]
    return len(held), sum(entry.size for entry in held)
