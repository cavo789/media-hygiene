"""A journal decoded once per version; `can_undo` checks a gone folder once."""

from __future__ import annotations

import os
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions import undoable
from media_hygiene.actions.journal import JournalEntry, JournalWriter, journal_file
from media_hygiene.actions.journal_cache import read_journal_once
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import new_run_id
from media_hygiene.actions.undoable import can_undo
from media_hygiene.errors import JournalError

if TYPE_CHECKING:
    from pathlib import Path


def _quarantined(seq: int, quarantine: Path) -> JournalEntry:
    """A file set aside in `quarantine`, done."""
    return JournalEntry(
        seq=seq,
        phase=Phase.CLEAN,
        status=Status.DONE,
        action=ActionKind.QUARANTINE,
        path=str(quarantine.parent / "photos" / f"{seq}.jpg"),
        host_path=f"C:\\{seq}.jpg",
        size=0,
        mtime_ns=1,
        quarantine=str(quarantine / f"{seq}.jpg"),
    )


def _write(file: Path, entries: list[JournalEntry]) -> None:
    """Append entries to a journal."""
    with JournalWriter.open(file) as journal:
        for entry in entries:
            journal.record(entry)


def test_appended_journal_is_read_again(tmp_path: Path) -> None:
    """An append changes the size: the new entry is seen."""
    file = journal_file(tmp_path, new_run_id(tmp_path))
    _write(file, [_quarantined(1, tmp_path / "q")])
    assert len(read_journal_once(file)) == 1
    _write(file, [_quarantined(2, tmp_path / "q")])
    assert len(read_journal_once(file)) == 2


def test_atomic_rewrite_and_touch_are_read_again(tmp_path: Path) -> None:
    """A new inode with the same size and time, or a `touch`, reads the file again."""
    file = journal_file(tmp_path, new_run_id(tmp_path))
    _write(file, [_quarantined(1, tmp_path / "q")])
    stamp = file.stat()
    read_journal_once(file)
    other = tmp_path / "other.jsonl"
    other.write_text(file.read_text("utf-8").replace('"seq":1', '"seq":7'), "utf-8")
    os.utime(other, ns=(stamp.st_atime_ns, stamp.st_mtime_ns))
    other.replace(file)
    assert read_journal_once(file)[0].seq == 7
    file.write_text(file.read_text("utf-8").replace('"seq":7', '"seq":8'), "utf-8")
    os.utime(file, ns=(stamp.st_atime_ns, stamp.st_mtime_ns + 1))
    assert read_journal_once(file)[0].seq == 8


def test_missing_journal_still_says_why(tmp_path: Path) -> None:
    """A journal that is not there raises as `read_journal` does."""
    with pytest.raises(JournalError):
        read_journal_once(tmp_path / "none.jsonl")


def test_gone_quarantine_folder_checked_once(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A purged run: one folder check, no check per file, and not undoable."""
    file = journal_file(tmp_path, new_run_id(tmp_path))
    _write(file, [_quarantined(seq, tmp_path / "gone") for seq in range(1, 50)])
    asked: list[object] = []

    def blocked(*args: object) -> str:
        asked.append(args)
        return "blocked"

    monkeypatch.setattr(undoable, "blocker", blocked)
    assert not can_undo(tmp_path, file.name.removesuffix(".jsonl"))
    assert not asked


def test_kept_quarantine_is_undoable(tmp_path: Path) -> None:
    """The quarantined copy is there: the run can be undone."""
    quarantine = tmp_path / "q"
    quarantine.mkdir()
    (quarantine / "1.jpg").write_bytes(b"")
    file = journal_file(tmp_path, new_run_id(tmp_path))
    _write(file, [_quarantined(1, quarantine)])
    assert can_undo(tmp_path, file.name.removesuffix(".jsonl"))
