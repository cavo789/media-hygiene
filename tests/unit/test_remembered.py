"""The contents set aside by a choice, as the journals remember them (TODO 0216).

The words of each journal are kept by the index: one test per event that changes a
journal (it grows, it goes, a line this version cannot read).
"""

from __future__ import annotations

import os
from datetime import UTC, datetime, timedelta
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.journal import JournalEntry, journal_file
from media_hygiene.actions.kinds import REMEMBERED, ActionKind, Phase, Status
from media_hygiene.actions.remembered import remembered_set
from media_hygiene.index.journal_words import read_signatures
from media_hygiene.index.repository import FactsRepository
from tests.support.journaled import done_line

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.plan.returned import RememberedSet

_START: Final = datetime(2026, 1, 1, tzinfo=UTC)
_DIGEST: Final = "ab" * 32


@pytest.fixture
def index() -> Iterator[sqlite3.Connection]:
    """A throw-away index."""
    with FactsRepository.open(None) as repository:
        yield repository.connection


def entry(seq: int, action: ActionKind, minutes: int) -> JournalEntry:
    """A `done` set-aside of one content, `minutes` after the start."""
    return done_line(
        action,
        f"/data/c/Photos/IMG_{seq}.jpg",
        seq=seq,
        host_path=f"C:\\Photos\\IMG_{seq}.jpg",
        size=1000,
        mtime_ns=1,
        sha256=_DIGEST,
        at=_START + timedelta(minutes=minutes),
    )


def undone(done: JournalEntry, minutes: int) -> JournalEntry:
    """The `done` undo of an action."""
    return done.model_copy(
        update={"phase": Phase.UNDO, "at": _START + timedelta(minutes=minutes)}
    )


def write(journal_dir: Path, run_id: str, *entries: JournalEntry) -> Path:
    """Append entries to a run's journal."""
    journal_dir.mkdir(exist_ok=True)
    path = journal_file(journal_dir, run_id)
    with path.open("a", encoding="utf-8") as lines:
        lines.writelines(item.model_dump_json() + "\n" for item in entries)
    return path


def remembered(journal_dir: Path, index: sqlite3.Connection) -> RememberedSet:
    """What the journals remember; read twice, the second time from the index."""
    first = remembered_set(journal_dir, index)
    assert remembered_set(journal_dir, index) == first
    return first


@pytest.mark.parametrize("kind", sorted(REMEMBERED))
def test_a_kind_set_aside_by_a_choice_is_remembered(
    tmp_path: Path, index: sqlite3.Connection, kind: ActionKind
) -> None:
    """Burst shots, near copies, files chosen or unwanted, files back again."""
    write(tmp_path, "run1", entry(1, kind, 0))
    said = remembered(tmp_path, index).by_digest[1000, _DIGEST]
    assert (said.run_id, said.action, said.host_path) == (
        "run1",
        kind,
        "C:\\Photos\\IMG_1.jpg",
    )


@pytest.mark.parametrize(
    "kind",
    [
        ActionKind.QUARANTINE_DUPLICATE,
        ActionKind.DELETE_DUPLICATE,
        ActionKind.QUARANTINE,
        ActionKind.QUARANTINE_SIDECAR,
        ActionKind.MOVE,
    ],
)
def test_copies_broken_files_and_moves_are_not(
    tmp_path: Path, index: sqlite3.Connection, kind: ActionKind
) -> None:
    """A copy's content is kept; a broken file is broken; a move keeps the file."""
    write(tmp_path, "run1", entry(1, kind, 0))
    assert not remembered(tmp_path, index)


def test_a_pending_action_is_not(tmp_path: Path, index: sqlite3.Connection) -> None:
    """Only what was done counts."""
    pending = entry(1, ActionKind.QUARANTINE_BURST, 0).model_copy(
        update={"status": Status.PENDING}
    )
    write(tmp_path, "run1", pending)
    assert not remembered(tmp_path, index)


def test_an_undo_forgets_and_a_later_set_aside_remembers_again(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """The last word wins, whatever run says it."""
    first = entry(1, ActionKind.QUARANTINE_BURST, 0)
    write(tmp_path, "run1", first, undone(first, 5))
    assert not remembered(tmp_path, index)
    write(tmp_path, "run2", entry(1, ActionKind.QUARANTINE_CHOSEN, 10))
    said = remembered(tmp_path, index).by_digest[1000, _DIGEST]
    assert (said.run_id, said.action) == ("run2", ActionKind.QUARANTINE_CHOSEN)


def test_set_aside_again_keeps_when_and_why_it_was_first(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """A file back, set aside again, still says the burst review of the first run."""
    write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    write(tmp_path, "run2", entry(1, ActionKind.QUARANTINE_RETURNED, 10))
    said = remembered(tmp_path, index).by_digest[1000, _DIGEST]
    assert (said.run_id, said.action) == ("run1", ActionKind.QUARANTINE_BURST)


def test_a_purged_run_still_counts(tmp_path: Path, index: sqlite3.Connection) -> None:
    """`purge` empties the quarantine, never the journal: no quarantine is read."""
    write(tmp_path / "journal", "run1", entry(1, ActionKind.QUARANTINE_NEAR, 0))
    assert remembered(tmp_path / "journal", index)


def test_a_journal_that_grows_is_read_again(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """An undo appended to a journal already kept by the index forgets the content."""
    first = entry(1, ActionKind.QUARANTINE_BURST, 0)
    path = write(tmp_path, "run1", first)
    assert remembered(tmp_path, index)
    write(tmp_path, "run1", undone(first, 5))
    assert not remembered(tmp_path, index)
    assert read_signatures(index)["run1"][0] == path.stat().st_size


def test_a_journal_touched_is_read_again(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """Same size, another modification time: read again, the same words."""
    path = write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    before = remembered(tmp_path, index)
    stat = path.stat()
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns + 1_000_000_000))
    assert remembered(tmp_path, index) == before
    assert read_signatures(index)["run1"][1] == path.stat().st_mtime_ns


def test_a_journal_gone_takes_its_words_along(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """A journal deleted by hand: nothing of it is remembered."""
    path = write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    assert remembered(tmp_path, index)
    path.unlink()
    assert not remembered(tmp_path, index)
    assert "run1" not in read_signatures(index)


def test_a_line_this_version_cannot_read_is_skipped(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """A newer kind or a corrupt line never stops an audit."""
    path = write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    with path.open("a", encoding="utf-8") as lines:
        lines.write('{"status":"done","action":"quarantine-burst","at":"x"}\n')
        lines.write("not json\n")
    assert len(remembered(tmp_path, index)) == 1


def test_no_journal_folder_remembers_nothing(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """Without a journal, nothing is remembered."""
    assert not remembered(tmp_path / "missing", index)


def test_an_unreadable_journal_is_not_kept_as_saying_nothing(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """A journal locked (an antivirus) is read again at the next audit."""
    if os.geteuid() == 0:
        pytest.skip("root reads every file")
    path = write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    path.chmod(0)
    try:
        assert not remembered_set(tmp_path, index)
        assert "run1" not in read_signatures(index)
    finally:
        path.chmod(0o644)
    assert remembered(tmp_path, index)


def test_bytes_that_are_not_utf8_never_stop_an_audit(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """A journal cut in the middle of a character: its other lines still count."""
    path = write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    with path.open("ab") as lines:
        lines.write(b'{"status":"done","action":"quarantine-burst","path":"\xff\n')
    assert len(remembered(tmp_path, index)) == 1


def test_a_new_reading_reads_every_journal_again(
    tmp_path: Path, index: sqlite3.Connection, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A version that reads journals differently never trusts the words kept."""
    write(tmp_path, "run1", entry(1, ActionKind.QUARANTINE_BURST, 0))
    remembered(tmp_path, index)
    monkeypatch.setattr("media_hygiene.actions.remembered.WORDS_VERSION", 2)
    assert remembered(tmp_path, index)
    assert read_signatures(index)["run1"][2] == 2


def test_a_gone_mark_is_remembered_by_its_partial_digest(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """Without a SHA-256, the partial digest names the content; its undo forgets."""
    mark = entry(1, ActionKind.QUARANTINE_BURST, 0).model_copy(
        update={"sha256": None, "partial": "cd" * 32}
    )
    write(tmp_path, "run1", mark)
    found = remembered(tmp_path, index)
    assert set(found.by_partial) == {(1000, "cd" * 32)}
    assert not found.by_digest
    write(tmp_path, "run1", undone(mark, 5))
    assert not remembered(tmp_path, index)


def test_an_undone_return_forgets_both_digests_of_a_mark(
    tmp_path: Path, index: sqlite3.Connection
) -> None:
    """A mark named by both digests: the undo of its return forgets both."""
    both = {"partial": "cd" * 32}
    mark = entry(1, ActionKind.MARK_GONE, 0).model_copy(update=both)
    back = entry(1, ActionKind.QUARANTINE_RETURNED, 10).model_copy(update=both)
    write(tmp_path, "run1", mark)
    write(tmp_path, "run2", back, undone(back, 20))
    assert not remembered(tmp_path, index)
