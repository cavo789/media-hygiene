"""The quarantine counted from the journal, not by a walk of the disk (TODO 0277)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.actions.journal import journal_file
from media_hygiene.actions.kinds import ActionKind, Phase
from media_hygiene.services.status_parts import quarantine_state
from tests.support.journaled import done_line

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.actions.journal import JournalEntry

_RUN = "20261020-143210"


def _write(journal_dir: Path, lines: list[JournalEntry]) -> None:
    """Write a run's journal."""
    journal_dir.mkdir(exist_ok=True)
    text = "".join(line.model_dump_json() + "\n" for line in lines)
    journal_file(journal_dir, _RUN).write_text(text, "utf-8")


def _folder(quarantine: Path) -> Path:
    """The run's folder in the quarantine, one small file in it."""
    folder = quarantine / _RUN / "c"
    folder.mkdir(parents=True)
    (folder / "a.jpg").write_bytes(b"x" * 5)
    return folder


def _set_aside(seq: int, size: int) -> JournalEntry:
    """A file of the run set aside."""
    path = f"/data/c/{seq}.jpg"
    return done_line(ActionKind.QUARANTINE, path, seq=seq, size=size)


def test_the_journal_gives_the_count_and_size_not_the_disk(tmp_path: Path) -> None:
    """Two set aside, one put back by undo: one file, its size from the journal."""
    quarantine, journal_dir = tmp_path / "quarantine", tmp_path / "journal"
    _folder(quarantine)
    first, second = _set_aside(1, 100), _set_aside(2, 200)
    put_back = second.model_copy(update={"phase": Phase.UNDO})
    _write(journal_dir, [first, second, put_back])
    state = quarantine_state([quarantine], journal_dir)
    assert [(run.run_id, run.files, run.size) for run in state.runs] == [(_RUN, 1, 100)]


def test_a_run_whose_folder_is_gone_is_not_counted(tmp_path: Path) -> None:
    """Purged, or its folder removed in the Explorer: its journal alone counts none."""
    quarantine, journal_dir = tmp_path / "quarantine", tmp_path / "journal"
    quarantine.mkdir()
    _write(journal_dir, [_set_aside(1, 100)])
    assert not quarantine_state([quarantine], journal_dir).runs


def test_a_run_without_its_journal_is_walked(tmp_path: Path) -> None:
    """No journal to read: the files on disk are counted and measured."""
    quarantine, journal_dir = tmp_path / "quarantine", tmp_path / "journal"
    _folder(quarantine)
    journal_dir.mkdir()
    state = quarantine_state([quarantine], journal_dir)
    assert [(run.files, run.size) for run in state.runs] == [(1, 5)]


def test_a_run_fully_undone_holds_nothing(tmp_path: Path) -> None:
    """Every file put back: the run leaves the list, whatever its folder holds."""
    quarantine, journal_dir = tmp_path / "quarantine", tmp_path / "journal"
    _folder(quarantine)
    line = _set_aside(1, 100)
    _write(journal_dir, [line, line.model_copy(update={"phase": Phase.UNDO})])
    assert not quarantine_state([quarantine], journal_dir).runs
