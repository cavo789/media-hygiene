"""`mh push --undo <run>`: the renames of a run put back on the target (0264).

The container reads the run's journal and the target (read-only) and writes the
renames back as `move` lines, each recorded `pending` (phase `undo`) before Windows
makes it; a second run sees them made and records them `done`. A rename whose file is
no longer where the run left it, or whose old place is taken (robocopy copied the
edited file there), is skipped and said. The copies stay: the backup keeps them.
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalWriter, latest_states, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import run_phase
from media_hygiene.actions.undo import actions_to_undo
from media_hygiene.errors import JournalError
from media_hygiene.i18n import _
from media_hygiene.services.push_journal import KINDS, push_run
from media_hygiene.services.push_lines import Order

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry
    from media_hygiene.services.push_journal import BackupRun
    from media_hygiene.services.push_place import Target

_RENAMES = frozenset(KINDS.values())


@dataclass(frozen=True, slots=True)
class UndoPlan:
    """The renames to make back, and those that cannot be."""

    lines: tuple[str, ...] = ()
    skipped: tuple[str, ...] = ()  # paths in the target, where the run left them
    copies: int = 0  # folders robocopy copied into: they stay


def plan_undo(journal_dir: Path, run_id: str, target: Target) -> UndoPlan:
    """Write back each rename of a run not undone yet, newest first.

    Args:
        journal_dir: Journal mount point.
        run_id: The run.
        target: The target it changed.

    Returns:
        The `move` lines for Windows; each recorded `pending` first.
    """
    run = _existing(journal_dir, run_id, target)
    every = read_journal(run.journal)
    entries = actions_to_undo(every)
    # The renames an undo stopped before its end recorded `pending`.
    tried = frozenset(latest_states(every, Phase.UNDO))
    lines: list[str] = []
    skipped: list[str] = []
    with JournalWriter.open(run.journal) as journal:
        for entry in reversed(entries):
            if entry.action not in _RENAMES or entry.status is not Status.DONE:
                continue
            line = _back(target, entry, tried=entry.seq in tried)
            if line is None:
                skipped.append(entry.target or "")
            elif line:
                journal.record(_undo(entry, Status.PENDING))
                lines.append(line)
            else:
                journal.record(_undo(entry, Status.DONE))  # made by that undo
    copies = sum(entry.action is ActionKind.PUSH_COPY for entry in entries)
    return UndoPlan(tuple(lines), tuple(skipped), copies)


def _back(target: Target, entry: JournalEntry, *, tried: bool) -> str | None:
    """The `move` line putting a rename back, when it can be.

    Args:
        target: The target.
        entry: The rename, `path` before and `target` after.
        tried: An undo stopped before its end recorded it `pending`.

    Returns:
        The line; empty when that undo made it already; None when the file is no
        longer where the run left it, or its old place is taken.
    """
    root = target.point
    after = entry.target or ""
    if tried and (root / entry.path).is_file() and not (root / after).exists():
        return ""
    if not (root / after).is_file() or (root / entry.path).exists():
        return None
    hosts = (target.host_of(after), target.host_of(entry.path))
    return "\t".join((Order.MOVE.value, *hosts, str(entry.size), str(entry.mtime_ns)))


def record_undone(journal_dir: Path, run_id: str, target: Target) -> int:
    """Write `done` each rename back that the target shows made.

    Args:
        journal_dir: Journal mount point.
        run_id: The run.
        target: The target it changed.

    Returns:
        How many renames are back.
    """
    run = _existing(journal_dir, run_id, target)
    root = target.point
    latest = latest_states(read_journal(run.journal), Phase.UNDO)
    back = [
        entry
        for entry in latest.values()
        if entry.status is Status.PENDING
        and (root / entry.path).is_file()
        and not (root / (entry.target or "")).is_file()
    ]
    with JournalWriter.open(run.journal) as journal:
        for entry in back:
            journal.record(entry.as_done())
    return len(back)


def _existing(journal_dir: Path, run_id: str, target: Target) -> BackupRun:
    """The run of `mh push` named, refusing any other.

    Args:
        journal_dir: Journal mount point.
        run_id: The run.
        target: The target.

    Returns:
        The run.

    Raises:
        JournalError: No such run, or one of another command.
    """
    run = push_run(journal_dir, run_id, target)
    if not run.journal.is_file() or run_phase(read_journal(run.journal)) is not (
        Phase.PUSH
    ):
        raise JournalError(_("Unknown run {run_id}.").format(run_id=run_id))
    return run


def _undo(entry: JournalEntry, status: Status) -> JournalEntry:
    """The `undo` twin of a rename.

    Args:
        entry: The rename, as the run recorded it.
        status: `pending` before Windows makes it, `done` when already made.

    Returns:
        The entry of phase `undo`, same number.
    """
    return entry.model_copy(update={"phase": Phase.UNDO, "status": status})
