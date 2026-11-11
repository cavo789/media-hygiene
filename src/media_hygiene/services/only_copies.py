"""The files set aside that exist nowhere else (0688): counted before a purge.

The quarantine holds exact copies, whose kept twin stays in the photo folders, and
files with no twin at all: near duplicates (`--tier near`), burst shots, junk,
unreadable files, intruders. A file is *covered* when it was set aside as an exact
copy (`quarantine-duplicate`: compared byte for byte with its `keeper` first) and
that kept copy is still on the disk with the same size; everything else is the only
copy (a near duplicate names a keeper too, of other content: not a cover). A run
whose journal is lost cannot tell: each of its files counts as an only copy (the
safe side). A NAS copy is not counted as cover: the container keeps no listing of
the push target.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import done_states, journal_file
from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.actions.purge import run_folders
from media_hygiene.actions.quarantine import QUARANTINED
from media_hygiene.actions.runs import run_phase
from media_hygiene.errors import JournalError

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.actions.journal import JournalEntry


@dataclass(frozen=True, slots=True)
class OnlyCopies:
    """The files of the quarantine with no other copy: where they are, their size."""

    files: tuple[Path, ...] = ()
    size: int = 0


def only_copies(
    quarantines: Sequence[Path], journal_dir: Path, runs: Sequence[str]
) -> OnlyCopies:
    """Find the files of these runs' quarantines that exist nowhere else.

    Args:
        quarantines: The default quarantine and the per-drive ones.
        journal_dir: Journal mount point.
        runs: The runs asked about.

    Returns:
        Their only copies, still on the disk, in the order of the runs.
    """
    files: list[Path] = []
    size = 0
    for run in runs:
        found = _of_run(quarantines, journal_dir, run)
        for file in found:
            try:
                size += file.stat().st_size
            except OSError:  # gone by hand meanwhile: nothing to lose any more
                continue
            files.append(file)
    return OnlyCopies(tuple(files), size)


def _of_run(quarantines: Sequence[Path], journal_dir: Path, run: str) -> list[Path]:
    """The only copies of one run: from its journal, else every file of its folders.

    Args:
        quarantines: The default quarantine and the per-drive ones.
        journal_dir: Journal mount point.
        run: The run.

    Returns:
        The files of its quarantine with no kept twin on the disk.
    """
    try:
        entries = read_journal_once(journal_file(journal_dir, run))
    except JournalError, OSError:
        folders = run_folders(quarantines, run)
        return sorted(p for f in folders for p in f.rglob("*") if p.is_file())
    return [
        Path(entry.quarantine)
        for entry in set_aside(entries)
        if entry.quarantine is not None and not _covered(entry)
    ]


def set_aside(entries: list[JournalEntry]) -> list[JournalEntry]:
    """The files a run set aside that undo did not put back.

    Args:
        entries: The run's journal entries.

    Returns:
        Their entries, with where each one is in the quarantine.
    """
    put_back = {entry.seq for entry in done_states(entries, Phase.UNDO)}
    return [
        entry
        for entry in done_states(entries, run_phase(entries))
        if entry.action in QUARANTINED
        and entry.seq not in put_back
        and entry.quarantine is not None
    ]


def _covered(entry: JournalEntry) -> bool:
    """Tell whether a file set aside has its kept twin on the disk.

    Args:
        entry: Its journal entry.

    Returns:
        True for an exact copy whose keeper is there with the same size.
    """
    if entry.action is not ActionKind.QUARANTINE_DUPLICATE or entry.keeper is None:
        return False
    try:
        return Path(entry.keeper).stat().st_size == entry.size
    except OSError:
        return False
