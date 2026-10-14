"""`undo` puts a few files back at a time, as `clean` set them aside (0161)."""

from __future__ import annotations

import threading
import time
from typing import TYPE_CHECKING, Final, override

import pytest

from media_hygiene.actions.journal import JournalEntry, JournalWriter, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.parallel import WORKERS
from media_hygiene.actions.restore import perform
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.actions.reversal import Reversal

_FILES: Final = 24
_RUN: Final = "20261014-090000"


class Clean:
    """A clean done by hand: files in two folders, each moved to the quarantine."""

    def __init__(self, root: Path) -> None:
        """Set aside `_FILES` files, journaled `pending` then `done`."""
        self.data = root / "data" / "c" / "Photos"
        self.run = root / "quarantine" / _RUN
        self.journal = root / f"{_RUN}.jsonl"
        self.content = {
            self.data / f"{index % 2}" / f"{index}.jpg": bytes([index]) * (index + 1)
            for index in range(_FILES)
        }
        with JournalWriter.open(self.journal) as writer:
            for seq, (path, data) in enumerate(self.content.items(), 1):
                quarantined = self.run / "c" / "Photos" / path.parent.name / path.name
                quarantined.parent.mkdir(parents=True, exist_ok=True)
                quarantined.write_bytes(data)
                path.parent.mkdir(parents=True, exist_ok=True)
                entry = JournalEntry(
                    seq=seq,
                    phase=Phase.CLEAN,
                    status=Status.PENDING,
                    action=ActionKind.QUARANTINE_DUPLICATE,
                    path=str(path),
                    host_path=str(path),
                    size=len(data),
                    mtime_ns=quarantined.stat().st_mtime_ns,
                    quarantine=str(quarantined),
                )
                writer.record(entry)
                writer.record(entry.as_done())

    def undo(self, progress: NullProgress | None = None) -> Outcome:
        """Undo the run."""
        entries = read_journal(self.journal)
        with JournalWriter.open(self.journal) as journal:
            return UndoExecutor(journal, progress or NullProgress()).run(entries)

    def back(self) -> int:
        """How many files are back, identical."""
        return sum(
            path.is_file() and path.read_bytes() == data
            for path, data in self.content.items()
        )


def test_a_few_files_come_back_at_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """More than one restore at a time, never more than the workers."""
    run = Clean(tmp_path)
    lock = threading.Lock()
    running = peak = 0

    def counted(entry: JournalEntry, reversal: Reversal) -> None:
        nonlocal running, peak
        with lock:
            running += 1
            peak = max(peak, running)
        time.sleep(0.01)
        perform(entry, reversal)
        with lock:
            running -= 1

    monkeypatch.setattr("media_hygiene.actions.undo.perform", counted)
    outcome = run.undo()
    assert outcome.done == _FILES
    assert outcome.bytes_done == sum(len(data) for data in run.content.values())
    assert not outcome.failed
    assert run.back() == _FILES
    assert 1 < peak <= WORKERS
    assert not run.run.exists()  # every emptied folder removed, once at the end


class _StopAfter(NullProgress):
    """A progress sink pressing Ctrl+C after a few files are shown."""

    def __init__(self, files: int) -> None:
        """Stop once `files` files are shown."""
        self._left = files

    @override
    def advance(self, weight: int = 1) -> None:
        """Count a file shown; Ctrl+C once enough are."""
        del weight
        self._left -= 1
        if not self._left:
            raise KeyboardInterrupt


def test_an_interrupted_undo_is_resumed_by_a_second_one(tmp_path: Path) -> None:
    """Ctrl+C: the files under way end, the others wait for the next undo."""
    run = Clean(tmp_path)
    with pytest.raises(KeyboardInterrupt):
        run.undo(_StopAfter(3))
    first = run.back()
    assert 3 <= first < _FILES
    entries = read_journal(run.journal)
    undone = [entry for entry in entries if entry.phase is Phase.UNDO]
    assert {entry.status for entry in undone} == {Status.PENDING, Status.DONE}
    assert len(undone) == 2 * first  # each file back has its `pending`, then `done`
    outcome = run.undo()
    assert outcome.done == _FILES - first
    assert not outcome.failed
    assert not outcome.skipped
    assert run.back() == _FILES
    assert not run.run.exists()


def test_an_undo_stopped_between_its_lines_is_judged_from_the_files(
    tmp_path: Path,
) -> None:
    """A file back whose `done` line is missing is reported there, not moved twice."""
    run = Clean(tmp_path)
    entries = read_journal(run.journal)
    last = entries[-1]
    quarantined = run.run / "c" / "Photos" / "1" / f"{_FILES - 1}.jpg"
    quarantined.rename(last.path)
    with JournalWriter.open(run.journal) as writer:
        writer.record(
            last.model_copy(update={"phase": Phase.UNDO, "status": Status.PENDING})
        )
    outcome = run.undo()
    assert outcome.done == _FILES - 1
    assert [incident.path.name for incident in outcome.skipped] == [f"{_FILES - 1}.jpg"]
    assert run.back() == _FILES
