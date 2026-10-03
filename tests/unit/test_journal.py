"""The write-ahead journal and the run history derived from it."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import (
    JournalEntry,
    JournalWriter,
    done_states,
    journal_file,
    latest_states,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import (
    list_run_ids,
    new_run_id,
    run_phase,
    summarize,
)
from media_hygiene.errors import JournalError

if TYPE_CHECKING:
    from pathlib import Path


def entry(seq: int, action: ActionKind, phase: Phase = Phase.CLEAN) -> JournalEntry:
    """Build a pending entry for a 100-byte file."""
    return JournalEntry(
        seq=seq,
        phase=phase,
        status=Status.PENDING,
        action=action,
        path=f"/data/c/{seq}.jpg",
        host_path=f"C:\\{seq}.jpg",
        size=100,
        mtime_ns=1,
    )


def test_history_counts_done_actions_and_restores(tmp_path: Path) -> None:
    """Only `done` actions count; undo entries count as restores."""
    run_id = new_run_id(tmp_path)
    with JournalWriter.open(journal_file(tmp_path, run_id)) as journal:
        for item in (
            entry(1, ActionKind.DELETE_DUPLICATE),
            entry(2, ActionKind.QUARANTINE),
        ):
            journal.record(item)
            journal.record(item.as_done())
        journal.record(entry(3, ActionKind.DELETE_EMPTY))
        journal.record(entry(1, ActionKind.DELETE_DUPLICATE, Phase.UNDO).as_done())
    summary = summarize(tmp_path, run_id)
    # The quarantined file still takes its space until `purge`: not freed.
    assert (summary.deleted, summary.quarantined, summary.freed, summary.restored) == (
        1,
        1,
        100,
        1,
    )
    entries = read_journal(journal_file(tmp_path, run_id))
    assert latest_states(entries, Phase.CLEAN)[3].status is Status.PENDING


def test_run_ids_are_unique_and_listed_newest_first(tmp_path: Path) -> None:
    """Two runs in the same second get distinct identifiers."""
    first = new_run_id(tmp_path)
    journal_file(tmp_path, first).write_text("")
    second = new_run_id(tmp_path)
    journal_file(tmp_path, second).write_text("")
    assert second == f"{first}-2"
    assert list_run_ids(tmp_path) == sorted([first, second], reverse=True)
    assert list_run_ids(tmp_path / "absent") == []


def test_missing_or_corrupt_journal(tmp_path: Path) -> None:
    """A missing journal or a corrupt line is a journal error."""
    with pytest.raises(JournalError, match="No journal"):
        read_journal(tmp_path / "absent.jsonl")
    corrupt = tmp_path / "corrupt.jsonl"
    corrupt.write_text(
        entry(1, ActionKind.DELETE_EMPTY).model_dump_json() + "\n\n{oops\n"
    )
    with pytest.raises(JournalError, match="Line 3"):
        read_journal(corrupt)


def test_an_action_this_version_does_not_know_is_explained(tmp_path: Path) -> None:
    """A journal written by a newer version names the problem and the remedy."""
    newer = tmp_path / "newer.jsonl"
    line = entry(1, ActionKind.MOVE).model_dump_json().replace('"move"', '"teleport"')
    newer.write_text(line + "\n")
    with pytest.raises(JournalError, match="does not know") as caught:
        read_journal(newer)
    assert caught.value.tip is not None


def test_a_sort_run_is_told_apart_and_counted(tmp_path: Path) -> None:
    """Moves are counted as moved, never as deleted nor freed; folders count nothing."""
    run_id = new_run_id(tmp_path)
    with JournalWriter.open(journal_file(tmp_path, run_id)) as journal:
        for item in (
            entry(1, ActionKind.CREATE_FOLDER, Phase.SORT),
            entry(2, ActionKind.MOVE, Phase.SORT),
            entry(3, ActionKind.MOVE, Phase.SORT),
            entry(4, ActionKind.REMOVE_FOLDER, Phase.SORT),
        ):
            journal.record(item)
            journal.record(item.as_done())
    summary = summarize(tmp_path, run_id)
    assert summary.kind is Phase.SORT
    assert (summary.moved, summary.deleted, summary.freed, summary.quarantined) == (
        2,
        0,
        0,
        0,
    )
    entries = read_journal(journal_file(tmp_path, run_id))
    assert [item.seq for item in done_states(entries, Phase.SORT)] == [1, 2, 3, 4]
    assert run_phase([]) is Phase.CLEAN
