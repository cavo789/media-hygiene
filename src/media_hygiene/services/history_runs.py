"""The runs `mh history` lists: the journal's, and those known only from a copy.

Each run's journal is copied beside its quarantine folder (0697). When `/journal`
lacks a run (the journal folder wiped, a new PC) but a mounted quarantine holds its
copy, the run is listed too, marked *from the quarantine* (0721): `mh undo <run>`
takes the copy back first, so the run is not invisible until then. A quarantine not
mounted, or a copy that does not read, adds nothing: no run is invented.
"""

from __future__ import annotations

import logging
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.journal_copy import copied_journals
from media_hygiene.actions.runs import newest_first, run_journals, summary_of
from media_hygiene.errors import JournalError, MountError
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.quarantines import mounted_quarantines

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.runs import RunSummary
    from media_hygiene.services.runtime import Runtime

_LOGGER: Final = logging.getLogger(__name__)


@dataclass(frozen=True, slots=True)
class HistoryRuns:
    """The runs to list, newest first, and those known only from a quarantine copy."""

    summaries: tuple[RunSummary, ...]
    copied: frozenset[str] = frozenset()


def load_runs(runtime: Runtime) -> HistoryRuns:
    """Read every run of the journal, and of the copies `/journal` lacks.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The runs, newest first.

    Raises:
        MountError: The journal is not mounted.
    """
    if not runtime.persistent(MountKind.JOURNAL):
        raise MountError(
            _("No journal mount: no history to show."),
            _('Mount the journal folder used by clean: -v "<folder>:/journal".'),
        )
    journals = run_journals(runtime.locations.journal_dir)
    summaries = {
        run: summary_of(read_journal_once(path), run) for run, path in journals.items()
    }
    copies = copied_journals(mounted_quarantines(runtime).folders)
    readable: dict[str, Path] = {}
    for run_id, copy in copies.items():
        if run_id in journals:
            continue  # the journal is the reference: listed once, unmarked
        summary = _summary_of_copy(copy, run_id)
        if summary is not None:
            summaries[run_id] = summary
            readable[run_id] = copy
    order = newest_first(journals | readable)
    return HistoryRuns(tuple(summaries[run] for run in order), frozenset(readable))


def _summary_of_copy(copy: Path, run_id: str) -> RunSummary | None:
    """Summarise a run from the copy of its journal, if it reads.

    Args:
        copy: `<quarantine>/<run>.jsonl`.
        run_id: The run.

    Returns:
        Its summary; None when the copy cannot be read or a line is corrupt.
    """
    try:
        return summary_of(read_journal_once(copy), run_id)
    except (JournalError, OSError, ValueError) as exc:  # ValueError: not UTF-8
        _LOGGER.warning("journal copy %s not listed: %s", copy, exc)
        return None
