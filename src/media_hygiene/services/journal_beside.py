"""Each run's journal copied beside its quarantine folder, and taken back (0697).

At the end of every run that writes to its journal (`clean`, `sort`, `shrink`, `undo`…)
the journal is copied beside the run's folder in each quarantine that holds one
(`actions/journal_copy`). A run with no folder there any more (never had one, or an
undo brought every file back) has no copy: a stale one is erased. When `/journal`
lacks a run that has a copy (the journal folder wiped, a new PC), `undo` puts the copy
back in `/journal` first — never over a journal — then reads it as any other.
"""

from __future__ import annotations

import logging
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.journal_copy import (
    found_copy,
    journal_copy,
    remove_copy,
    write_copy,
)
from media_hygiene.actions.purge import run_folders
from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.constants import JOURNAL_SUFFIX
from media_hygiene.i18n import _
from media_hygiene.services.quarantines import mounted_quarantines
from media_hygiene.services.run_listings import forget_run_listings

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.kinds import Phase
    from media_hygiene.services.runtime import Runtime

_LOGGER: Final = logging.getLogger(__name__)


def copy_beside(runtime: Runtime, run_id: str) -> None:
    """Copy a run's journal beside its folder in every quarantine holding one.

    A copy that fails is said, never fatal: the journal in `/journal` stays the
    reference, and the run's files are where it says.

    Args:
        runtime: Settings, mount points and output.
        run_id: The run just written.
    """
    journal = journal_file(runtime.locations.journal_dir, run_id)
    if not journal.is_file():
        return
    quarantines = mounted_quarantines(runtime).folders
    holding = {folder.parent for folder in run_folders(quarantines, run_id)}
    for quarantine in quarantines:
        try:
            if quarantine in holding:
                write_copy(journal, journal_copy(quarantine, run_id))
            else:
                remove_copy(quarantine, run_id)  # nothing of the run left there
        except OSError as exc:
            _LOGGER.warning("journal copy of %s in %s: %s", run_id, quarantine, exc)
            runtime.output.warning(
                _(
                    "The copy of the journal of run {run} beside its quarantine "
                    "could not be written: {reason}. The journal itself is safe."
                ).format(run=run_id, reason=exc.strerror or exc)
            )


def take_back_journals(runtime: Runtime) -> list[str]:
    """Put back in `/journal` the copies of the runs it lacks.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The runs whose journal came back from its quarantine, read back.
    """
    journal_dir = runtime.locations.journal_dir
    quarantines = mounted_quarantines(runtime).folders
    back: list[str] = []
    for run_id in sorted(_copied_runs(quarantines)):
        journal = journal_file(journal_dir, run_id)
        copy = found_copy(quarantines, run_id)
        if journal.exists() or copy is None:
            continue  # never over a journal
        try:
            journal_dir.mkdir(parents=True, exist_ok=True)
            write_copy(copy, journal)
        except OSError as exc:
            _LOGGER.warning("journal of %s from %s: %s", run_id, copy, exc)
            continue
        runtime.output.info(
            _("Journal of run {run} taken back from its quarantine: {path}").format(
                run=run_id, path=runtime.mapper.to_host(copy)
            )
        )
        back.append(run_id)
    return back


def _copied_runs(quarantines: tuple[Path, ...]) -> set[str]:
    """The runs with a copy of their journal in a quarantine.

    Args:
        quarantines: The default quarantine and the per-drive ones.

    Returns:
        Their identifiers.
    """
    runs: set[str] = set()
    for folder in quarantines:
        if not folder.is_dir():
            continue
        for copy in folder.glob(f"*{JOURNAL_SUFFIX}"):
            run_id = copy.name.removesuffix(JOURNAL_SUFFIX)
            if RUN_ID_PATTERN.fullmatch(run_id) and copy.is_file():
                runs.add(run_id)
    return runs


def run_ended(runtime: Runtime, run_id: str, phase: Phase) -> None:
    """What every run does once its moves are done: listings read again, journal copied.

    Args:
        runtime: Settings, mount points and output.
        run_id: The run.
        phase: The command that ran it.
    """
    forget_run_listings(runtime, run_id, phase)
    copy_beside(runtime, run_id)
