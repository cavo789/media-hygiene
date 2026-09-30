"""Which rows of a plan earlier sort runs moved, from their journals."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalEntry, JournalWriter, journal_file
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.sort_resume import moved_rows

if TYPE_CHECKING:
    from pathlib import Path


def move(seq: int, row: str, paths: tuple[Path, Path]) -> JournalEntry:
    """A pending move of plan `p`."""
    return JournalEntry(
        seq=seq,
        phase=Phase.SORT,
        status=Status.PENDING,
        action=ActionKind.MOVE,
        path=str(paths[0]),
        host_path=str(paths[0]),
        size=1,
        mtime_ns=0,
        target=str(paths[1]),
        plan="p",
        row=row,
    )


def test_done_and_carried_out_moves_count_undone_ones_do_not(tmp_path: Path) -> None:
    """Killed after the rename, before `done`: the file is at its target, it counts."""
    (tmp_path / "carried.jpg").write_bytes(b"x")
    (tmp_path / "never.jpg").write_bytes(b"x")
    done = move(1, "done", (tmp_path / "a", tmp_path / "b"))
    undone = move(2, "undone", (tmp_path / "c", tmp_path / "d"))
    carried = move(3, "carried", (tmp_path / "gone.jpg", tmp_path / "carried.jpg"))
    never = move(4, "never", (tmp_path / "never.jpg", tmp_path / "e"))
    other = move(5, "other", (tmp_path / "f", tmp_path / "g")).model_copy(
        update={"plan": "q", "status": Status.DONE}
    )
    with JournalWriter.open(journal_file(tmp_path, "run")) as journal:
        for entry in (done, undone):
            journal.record(entry.as_done())
        for entry in (carried, never, other):
            journal.record(entry)
        journal.record(undone.model_copy(update={"phase": Phase.UNDO}).as_done())
    with JournalWriter.open(journal_file(tmp_path, "clean")) as journal:
        journal.record(
            done.model_copy(update={"phase": Phase.CLEAN, "row": "clean"}).as_done()
        )
    assert moved_rows(tmp_path, "p") == {"done", "carried"}
