"""Journaled changes of a run: a `pending` line, the change, a `done` line."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalEntry
from media_hygiene.actions.kinds import Phase, Status
from media_hygiene.actions.quarantine import move_verified
from media_hygiene.scan.hashing import full_digest

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.actions.journal import JournalWriter
    from media_hygiene.actions.kinds import ActionKind
    from media_hygiene.actions.outcome import Tally
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.progress import ProgressSink


@dataclass(frozen=True, slots=True)
class CleanContext:
    """Where and how a run acts, and which command it is (`clean` by default)."""

    journal: JournalWriter
    mapper: HostPathMapper
    quarantine_run_dir: Path
    progress: ProgressSink
    phase: Phase = Phase.CLEAN


class JournaledChanges:
    """Numbers, journals and counts every change of one run."""

    def __init__(self, context: CleanContext, tally: Tally) -> None:
        """Prepare the changes of a run.

        Args:
            context: Journal, path mapper, quarantine folder and progress sink.
            tally: Counters of the run, updated after each change.
        """
        self._context = context
        self._tally = tally
        self._seq = 0

    def entry(self, file: MediaFile, action: ActionKind) -> JournalEntry:
        """Build the `pending` journal entry of an action.

        Args:
            file: File acted upon.
            action: What is about to happen.

        Returns:
            The entry, with the next sequence number.
        """
        self._seq += 1
        return JournalEntry(
            seq=self._seq,
            phase=self._context.phase,
            status=Status.PENDING,
            action=action,
            path=str(file.path),
            host_path=self._context.mapper.to_host(file.path),
            size=file.size,
            mtime_ns=file.mtime_ns,
        )

    def record(self, entry: JournalEntry, change: Callable[[], object]) -> None:
        """Journal `pending`, change, then journal `done`; count nothing.

        Args:
            entry: The pending entry.
            change: Zero-argument callable performing the change.
        """
        self._context.journal.record(entry)
        change()
        self._context.journal.record(entry.as_done())

    def act(self, entry: JournalEntry, change: Callable[[], object]) -> None:
        """Journal `pending`, change, journal `done`, then count the file.

        Args:
            entry: The pending entry.
            change: Zero-argument callable performing the change.
        """
        self.record(entry, change)
        self._tally.done += 1
        self._tally.bytes_done += entry.size

    def quarantine(
        self, file: MediaFile, action: ActionKind, keeper: Path | None = None
    ) -> None:
        """Move a file to this run's quarantine, journaled.

        Args:
            file: File to move.
            action: Why it is moved.
            keeper: The file kept instead, when there is one.
        """
        path = file.path
        target = self._context.quarantine_run_dir / self._context.mapper.relative(path)
        entry = self.entry(file, action).model_copy(
            update={
                "quarantine": str(target),
                "sha256": full_digest(path),
                "keeper": str(keeper) if keeper else None,
            },
        )
        self.act(entry, lambda: move_verified(path, target))
        self._tally.quarantined += 1
