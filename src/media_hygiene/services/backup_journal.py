r"""The journal of `mh backup`: `pending` before Windows renames, `done` after (0264).

A run of kind `backup`, written ahead as `clean` writes: each rename on the target (a
move, a set-aside in `.removed`) is recorded `pending` before `mh` makes it, then
`done` when the target, listed again, shows it made; the bytes robocopy copied are
recorded per photo folder. Paths are relative to the target (`C/Photos/a.jpg`), the
host path is Windows's. Nothing is ever written on the target by the container.
"""

from __future__ import annotations

from dataclasses import dataclass
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.journal import (
    JournalEntry,
    JournalWriter,
    journal_file,
    latest_states,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import RUN_ID_PATTERN
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _
from media_hygiene.services.backup_lines import Order

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping
    from pathlib import Path

    from media_hygiene.services.backup_lines import Change
    from media_hygiene.services.backup_place import Target

KINDS: Final[Mapping[Order, ActionKind]] = MappingProxyType(
    {
        Order.MOVE: ActionKind.BACKUP_MOVE,
        Order.ASIDE: ActionKind.BACKUP_ASIDE,
        Order.REMOVE: ActionKind.BACKUP_REMOVE,
    }
)


@dataclass(frozen=True, slots=True)
class BackupRun:
    """A run of `mh backup`: its journal, and the target it changed."""

    journal: Path
    target: Target

    @property
    def run_id(self) -> str:
        """Its identifier: the journal's name.

        Returns:
            It.
        """
        return self.journal.stem


def backup_run(journal_dir: Path, run_id: str, target: Target) -> BackupRun:
    """Name the journal of a run, refusing an identifier that is none.

    Args:
        journal_dir: Journal mount point.
        run_id: The run, as the plan named it.
        target: The target.

    Returns:
        The run.

    Raises:
        JournalError: The identifier is not one of a run.
    """
    if RUN_ID_PATTERN.fullmatch(run_id) is None:
        raise JournalError(_("Unknown run {run_id}.").format(run_id=run_id))
    journal_dir.mkdir(parents=True, exist_ok=True)
    return BackupRun(journal_file(journal_dir, run_id), target)


def record_pending(run: BackupRun, changes: Iterable[Change]) -> int:
    """Write each rename `pending`, on the disk before Windows makes it.

    Args:
        run: The run; its journal must not exist yet.
        changes: The moves and set-asides of the plan.

    Returns:
        How many were written.

    Raises:
        JournalError: The run was started already.
    """
    if run.journal.exists():
        raise JournalError(
            _("The run {run_id} was started already.").format(run_id=run.run_id)
        )
    written = 0
    with JournalWriter.open(run.journal) as journal:
        for seq, change in enumerate(changes, 1):
            journal.record(
                JournalEntry(
                    seq=seq,
                    phase=Phase.BACKUP,
                    status=Status.PENDING,
                    action=KINDS[change.order],
                    path=change.old.path,
                    host_path=run.target.host_of(change.old.path),
                    size=change.old.stat.size,
                    mtime_ns=change.old.stat.mtime_ns,
                    target=change.new,
                )
            )
            written = seq
    return written


def record_done(run: BackupRun, copied: Mapping[str, int]) -> tuple[JournalEntry, ...]:
    """Write `done` each rename the target shows made, and the bytes copied.

    Args:
        run: The run.
        copied: The bytes robocopy copied, by photo folder (its path in the target).

    Returns:
        The renames written `done`.
    """
    entries = read_journal(run.journal) if run.journal.is_file() else []
    latest = latest_states(entries, Phase.BACKUP)
    made = [
        entry
        for entry in latest.values()
        if entry.status is Status.PENDING and _made(run.target.point, entry)
    ]
    copies = {folder: size for folder, size in copied.items() if size}
    if not made and not copies:
        return ()
    first = max(latest, default=0) + 1
    with JournalWriter.open(run.journal) as journal:
        for entry in made:
            journal.record(entry.as_done())
        for seq, (folder, size) in enumerate(sorted(copies.items()), first):
            journal.record(_copied(run, seq, (folder, size)))
    return tuple(made)


def _copied(run: BackupRun, seq: int, copied: tuple[str, int]) -> JournalEntry:
    """The record of the bytes robocopy copied into one folder of the target.

    Args:
        run: The run.
        seq: Its number in the journal.
        copied: The folder (relative to the target) and its bytes.

    Returns:
        The entry, `done`: a fact, nothing waits for it.
    """
    folder, size = copied
    return JournalEntry(
        seq=seq,
        phase=Phase.BACKUP,
        status=Status.DONE,
        action=ActionKind.BACKUP_COPY,
        path=folder,
        host_path=run.target.host_of(folder),
        size=size,
        mtime_ns=0,
    )


def _made(root: Path, entry: JournalEntry) -> bool:
    """Tell whether the target shows a rename made.

    Args:
        root: The target in the container.
        entry: The rename, `path` before and `target` after.

    Returns:
        True when the file is at its new path, and no longer at its old one but
        for a set-aside, whose path robocopy fills again with the edited file.
    """
    if entry.target is None or not (root / entry.target).is_file():
        return False
    return entry.action is ActionKind.BACKUP_ASIDE or not (root / entry.path).exists()
