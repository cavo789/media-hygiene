"""Why each file of the backup the PC no longer has is gone, from what the tool knows.

By the file's path on the PC (0264): the journals of `clean` (set aside in a quarantine
still there or purged since, deleted as an exact copy, a deletion in the Explorer
confirmed in `review --gone`), then the deletions the audit found, waiting for
`review --gone` (the index, 0224). A run undone since is no reason: the file came back.
Without a journal mount, every file is `unknown`: nothing is proposed for removal.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import JournalEntry, journal_file, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.purge import runs_in
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.runs import list_run_ids
from media_hygiene.actions.undo import actions_to_undo
from media_hygiene.errors import JournalError
from media_hygiene.index.gone_rows import gone_records
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.plan.backup_gone import GoneReason
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_DELETED: Final = frozenset({ActionKind.DELETE_DUPLICATE, ActionKind.DELETE_EMPTY})


def gone_reasons(runtime: Runtime, paths: Mapping[str, Path]) -> dict[str, GoneReason]:
    """Tell why each file is gone from the PC.

    Args:
        runtime: Settings, mount points and output.
        paths: Each file of the backup gone from the PC (its path relative to the
            target), with its path on the PC (container).

    Returns:
        The reason of each file the tool knows; the others are left out (`unknown`).
    """
    if not paths or not runtime.persistent(MountKind.JOURNAL):
        return {}
    known = _from_journals(runtime)
    index = runtime.index_file
    if index is not None and index.is_file():
        with FactsRepository.open(index) as repository:
            for record in gone_records(repository.connection):
                known.setdefault(record.path, GoneReason.PENDING)
    found = {relative: known.get(str(path)) for relative, path in paths.items()}
    return {relative: reason for relative, reason in found.items() if reason}


def _from_journals(runtime: Runtime) -> dict[str, GoneReason]:
    """Read what the runs of `clean` did to each file, the newest run first.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The reason of each container path a run of `clean` removed.
    """
    journal_dir = runtime.locations.journal_dir
    held = frozenset(runs_in(mounted_quarantines(runtime).folders))
    known: dict[str, GoneReason] = {}
    for run_id in list_run_ids(journal_dir):
        journal = journal_file(journal_dir, run_id)
        if _first_phase(journal) is not Phase.CLEAN:
            continue  # a sort, a backup… removed nothing: never read whole
        try:
            entries = read_journal(journal)
        except JournalError:
            continue  # unreadable: its files stay `unknown`, never removed
        for entry in actions_to_undo(entries):
            reason = _reason(entry, in_quarantine=run_id in held)
            if reason is not None:
                known.setdefault(entry.path, reason)
    return known


def _reason(entry: JournalEntry, *, in_quarantine: bool) -> GoneReason | None:
    """The reason a done action of `clean` gives its file.

    Args:
        entry: The latest state of an action not undone.
        in_quarantine: Whether its run still has a quarantine.

    Returns:
        The reason; None for an action not done, or one that removed nothing.
    """
    if entry.status is not Status.DONE:
        return None
    if entry.action is ActionKind.MARK_GONE:
        return GoneReason.CONFIRMED
    if entry.action in _DELETED:
        return GoneReason.PURGED
    if entry.action in QUARANTINED:
        return GoneReason.QUARANTINE if in_quarantine else GoneReason.PURGED
    return None


def _first_phase(journal: Path) -> Phase | None:
    """The phase of a journal's first entry, without reading the rest.

    Args:
        journal: A run's journal.

    Returns:
        It; None when the first line cannot be read.
    """
    try:
        with journal.open(encoding="utf-8") as lines:
            first = lines.readline()
        return JournalEntry.model_validate_json(first).phase
    except OSError, ValueError:
        return None
