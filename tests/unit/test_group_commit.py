"""The journal syncs a `pending` line before its action, several at once (0171)."""

from __future__ import annotations

import os
import threading
import time
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalEntry, JournalWriter, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

WORKERS = 4
PER_WORKER = 25


def _entry(seq: int) -> JournalEntry:
    """A `pending` move.

    Args:
        seq: Its sequence number.

    Returns:
        The entry.
    """
    return JournalEntry(
        seq=seq,
        phase=Phase.SORT,
        status=Status.PENDING,
        action=ActionKind.MOVE,
        path=f"/data/c/{seq}.jpg",
        host_path=f"C:\\{seq}.jpg",
        size=seq,
        mtime_ns=1,
    )


class SyncedSizes:
    """A slow `fsync` noting how much of the journal each call covered."""

    def __init__(self, journal: Path) -> None:
        """Watch one journal.

        Args:
            journal: Its path.
        """
        self.journal = journal
        self.sizes: list[int] = []
        self._fsync = os.fsync

    def __call__(self, fd: int) -> None:
        """Note the size on disk, wait like a slow disk, then sync.

        Args:
            fd: The journal's descriptor.
        """
        size = self.journal.stat().st_size
        time.sleep(0.002)
        self._fsync(fd)
        self.sizes.append(size)

    def synced(self) -> int:
        """The bytes known to be on the disk.

        Returns:
            The size the last `fsync` covered.
        """
        return max(self.sizes, default=0)


def _watched(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> SyncedSizes:
    """Replace the journal's `fsync` by a watched one.

    Args:
        tmp_path: The test folder.
        monkeypatch: Pytest's patcher.

    Returns:
        The watcher.
    """
    watcher = SyncedSizes(tmp_path / "run.jsonl")
    monkeypatch.setattr("media_hygiene.actions.group_commit.os.fsync", watcher)
    return watcher


def test_a_pending_line_is_synced_before_record_returns_a_done_one_waits(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Write-ahead kept; the `done` line rides on the next sync, or on close."""
    watcher = _watched(tmp_path, monkeypatch)
    with JournalWriter.open(watcher.journal) as writer:
        writer.record(_entry(1))
        assert watcher.synced() == watcher.journal.stat().st_size
        writer.record(_entry(1).as_done())
        assert writer.syncs == 1
        assert watcher.synced() < watcher.journal.stat().st_size
        writer.record(_entry(2))
        assert writer.syncs == 2  # the `done` line went with it
        assert watcher.synced() == watcher.journal.stat().st_size
        writer.record(_entry(2).as_done())
    assert watcher.synced() == watcher.journal.stat().st_size  # closing syncs
    statuses = [entry.status for entry in read_journal(watcher.journal)]
    assert statuses == [Status.PENDING, Status.DONE] * 2


def test_workers_share_syncs_and_each_line_is_on_disk_when_record_returns(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Four workers, a slow disk: fewer syncs than lines, none returning early."""
    watcher = _watched(tmp_path, monkeypatch)
    early: list[int] = []
    lock = threading.Lock()

    def worker(first: int) -> None:
        for seq in range(first, first + PER_WORKER):
            writer.record(_entry(seq))
            line = f'"seq":{seq},'
            text = watcher.journal.read_text(encoding="utf-8")
            end = text.index("\n", text.index(line)) + 1
            if len(text[:end].encode()) > watcher.synced():
                with lock:
                    early.append(seq)

    with (
        JournalWriter.open(watcher.journal) as writer,
        ThreadPoolExecutor(WORKERS) as pool,
    ):
        list(pool.map(worker, range(1, WORKERS * PER_WORKER, PER_WORKER)))
        syncs = writer.syncs
    assert not early
    assert syncs < WORKERS * PER_WORKER
    seqs = sorted(entry.seq for entry in read_journal(watcher.journal))
    assert seqs == list(range(1, WORKERS * PER_WORKER + 1))
