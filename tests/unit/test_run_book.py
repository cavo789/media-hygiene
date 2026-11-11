"""The facts of each run kept in `/cache`, and the window of runs offered to undo."""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import JournalEntry, JournalWriter, journal_file
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.services import run_book
from media_hygiene.services.run_book import FACTS_FILE, RunBook, read_runs
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from pathlib import Path

_NOW = datetime(2026, 11, 11, 12, tzinfo=UTC)


def _run(book: RunBook, run_id: str, days_ago: int) -> Path:
    """A clean run that set one file aside, its copy still in the quarantine."""
    quarantine = book.journal_dir.parent / "q" / run_id
    quarantine.mkdir(parents=True)
    (quarantine / "a.jpg").write_bytes(b"x")
    line = done_line(
        ActionKind.QUARANTINE,
        str(book.journal_dir.parent / "photos" / run_id / "a.jpg"),
        size=1,
        quarantine=str(quarantine / "a.jpg"),
        at=_NOW - timedelta(days=days_ago),
    )
    file = journal_file(book.journal_dir, run_id)
    _append(file, line)
    return file


def _append(file: Path, line: JournalEntry) -> None:
    """Append one line to a journal."""
    with JournalWriter.open(file) as journal:
        journal.record(line)


@pytest.fixture
def book(tmp_path: Path) -> RunBook:
    """Journals and their kept facts in `tmp_path`."""
    journals = tmp_path / "journal"
    journals.mkdir()
    return RunBook(journals, tmp_path / FACTS_FILE)


def test_window_keeps_the_week_and_the_newest(book: RunBook) -> None:
    """Runs older than a week are not offered, but the newest one always is."""
    _run(book, "20261110-100000", 1)
    _run(book, "20261020-100000", 22)
    runs = read_runs(book, _NOW)
    assert [run.run_id for run in runs.facts] == ["20261110-100000", "20261020-100000"]
    assert [run.run_id for run in runs.undoable] == ["20261110-100000"]
    alone = RunBook(book.journal_dir.parent / "other", None)
    alone.journal_dir.mkdir()
    _run(alone, "20261001-100000", 41)
    assert [run.run_id for run in read_runs(alone, _NOW).undoable] == [
        "20261001-100000"
    ]


def test_kept_facts_spare_the_journal_reads(
    book: RunBook, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A second reading draws nothing from the journals; the quarantine census too."""
    _run(book, "20261110-100000", 1)
    first = read_runs(book, _NOW)
    assert book.store is not None
    assert book.store.is_file()
    assert first.facts[0].held == (1, 1)

    def refused(_file: Path) -> list[JournalEntry]:
        raise AssertionError

    monkeypatch.setattr(run_book, "read_journal_once", refused)
    assert read_runs(book, _NOW).facts == first.facts


def test_appended_or_touched_journal_is_drawn_again(book: RunBook) -> None:
    """An undo appended, or a journal touched, gives fresh facts."""
    file = _run(book, "20261110-100000", 1)
    read_runs(book, _NOW)
    undone = done_line(ActionKind.QUARANTINE, "/x", size=1).model_copy(
        update={"phase": Phase.UNDO}
    )
    _append(file, undone)
    assert read_runs(book, _NOW).facts[0].summary.restored == 1
    other = _run(book, "20261109-100000", 2)
    read_runs(book, _NOW)
    stamp = other.stat()  # the same size, another content, touched
    other.write_text(other.read_text("utf-8").replace('"size":1', '"size":7'), "utf-8")
    os.utime(other, ns=(stamp.st_atime_ns, stamp.st_mtime_ns + 1))
    assert read_runs(book, _NOW).facts[1].held == (1, 7)


def test_removed_journal_drops_out(book: RunBook) -> None:
    """A journal deleted by hand leaves the facts kept."""
    _run(book, "20261110-100000", 1)
    gone = _run(book, "20261109-100000", 2)
    read_runs(book, _NOW)
    gone.unlink()
    assert [run.run_id for run in read_runs(book, _NOW).facts] == ["20261110-100000"]
    assert book.store is not None
    assert "20261109-100000" not in book.store.read_text("utf-8")


def test_unreadable_store_is_drawn_again(book: RunBook) -> None:
    """A damaged facts file is ignored, then rewritten."""
    _run(book, "20261110-100000", 1)
    assert book.store is not None
    book.store.write_text("{not json", "utf-8")
    assert read_runs(book, _NOW).facts[0].held == (1, 1)
    assert book.store.read_text("utf-8").startswith("{")
