"""A run stopped during an action: `undo` tells what happened from the files."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalEntry, JournalWriter, read_journal
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.outcome import Outcome

_CONTENT = b"a video"


def _pending(tmp_path: Path, name: str) -> JournalEntry:
    """A quarantine move journaled `pending` only: the run stopped there.

    Args:
        tmp_path: The test folder.
        name: The file name.

    Returns:
        The entry.
    """
    return JournalEntry(
        seq=len(name),
        phase=Phase.CLEAN,
        status=Status.PENDING,
        action=ActionKind.QUARANTINE_DUPLICATE,
        path=str(tmp_path / "photos" / name),
        host_path=name,
        size=len(_CONTENT),
        mtime_ns=1,
        quarantine=str(tmp_path / "quarantine" / name),
    )


def _undo(tmp_path: Path, *entries: JournalEntry) -> Outcome:
    """Journal the entries, then undo them.

    Args:
        tmp_path: The test folder.
        *entries: The journaled actions.

    Returns:
        What the undo did.
    """
    journal = tmp_path / "run.jsonl"
    with JournalWriter.open(journal) as writer:
        for entry in entries:
            writer.record(entry)
    with JournalWriter.open(journal) as writer:
        return UndoExecutor(writer, NullProgress()).run(read_journal(journal))


def test_an_action_stopped_before_acting_is_neither_undone_nor_reported(
    tmp_path: Path,
) -> None:
    """The file is still in place: nothing happened, nothing to warn about."""
    entry = _pending(tmp_path, "stayed.mp4")
    original = tmp_path / "photos" / "stayed.mp4"
    original.parent.mkdir()
    original.write_bytes(_CONTENT)
    outcome = _undo(tmp_path, entry)
    assert outcome.done == 0
    assert not outcome.skipped
    assert not outcome.failed
    assert original.read_bytes() == _CONTENT


def test_an_action_stopped_before_its_done_line_is_undone(tmp_path: Path) -> None:
    """The file reached the quarantine: it comes back."""
    entry = _pending(tmp_path, "moved.mp4")
    quarantined = tmp_path / "quarantine" / "moved.mp4"
    quarantined.parent.mkdir()
    quarantined.write_bytes(_CONTENT)
    (tmp_path / "photos").mkdir()
    outcome = _undo(tmp_path, entry)
    assert outcome.done == 1
    assert (tmp_path / "photos" / "moved.mp4").read_bytes() == _CONTENT


def test_an_undo_carried_out_to_the_end_leaves_no_folder_in_the_quarantine(
    tmp_path: Path,
) -> None:
    """Every file back: the mirrored folders and the run's folder are gone too."""
    run = tmp_path / "quarantine" / "20261003-181738"
    original = tmp_path / "data" / "c" / "Photos" / "2014" / "clip.mp4"
    quarantined = run / "c" / "Photos" / "2014" / "clip.mp4"
    quarantined.parent.mkdir(parents=True)
    quarantined.write_bytes(_CONTENT)
    original.parent.mkdir(parents=True)
    entry = _pending(tmp_path, "clip.mp4").model_copy(
        update={"path": str(original), "quarantine": str(quarantined)}
    )
    outcome = _undo(tmp_path, entry, entry.as_done())
    assert outcome.done == 1
    assert original.read_bytes() == _CONTENT
    assert not run.exists()
    assert (tmp_path / "quarantine").is_dir()  # the mount point itself stays


def test_a_quarantine_folder_still_holding_a_file_stays(tmp_path: Path) -> None:
    """A file left in the quarantine (skipped, not undone) keeps its folders."""
    run = tmp_path / "quarantine" / "run"
    left = run / "photos" / "left.mp4"
    left.parent.mkdir(parents=True)
    left.write_bytes(_CONTENT)
    entry = _pending(tmp_path, "back.mp4").model_copy(
        update={"quarantine": str(run / "photos" / "back.mp4")}
    )
    (run / "photos" / "back.mp4").write_bytes(_CONTENT)
    (tmp_path / "photos").mkdir()
    _undo(tmp_path, entry, entry.as_done())
    assert left.read_bytes() == _CONTENT


def test_several_actions_stopped_at_once_are_each_judged(tmp_path: Path) -> None:
    """A clean handles a few files at once (0149): a stop leaves several `pending`.

    The one that reached the quarantine comes back; the one still in place is left.
    """
    moved, stayed = _pending(tmp_path, "a.mp4"), _pending(tmp_path, "bb.mp4")
    quarantined = tmp_path / "quarantine" / "a.mp4"
    quarantined.parent.mkdir()
    quarantined.write_bytes(_CONTENT)
    original = tmp_path / "photos" / "bb.mp4"
    original.parent.mkdir()
    original.write_bytes(_CONTENT)
    outcome = _undo(tmp_path, moved, stayed)
    assert outcome.done == 1
    assert not outcome.failed
    assert (tmp_path / "photos" / "a.mp4").read_bytes() == _CONTENT
    assert original.read_bytes() == _CONTENT
