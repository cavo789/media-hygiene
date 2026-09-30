"""Undo reverses a sort run: files moved back, folders recreated and removed."""

from __future__ import annotations

import hashlib
import os
from types import MappingProxyType
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import (
    JournalEntry,
    JournalWriter,
    journal_file,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.plan_runs import runs_of_plan
from media_hygiene.actions.reversal import REVERSALS
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.errors import JournalError
from media_hygiene.scan.progress import NullProgress
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.actions.outcome import Outcome
    from media_hygiene.paths.locations import Locations

MTIME = 1_500_000_000_000_000_000


class SortRun:
    """A sort done by hand, journaled as `sort` will journal it (0028)."""

    def __init__(self, root: Path, journal_dir: Path | None = None) -> None:
        """Two photos in `2016/Juillet 2016`, sorted into `Tri/2016/Vacances`."""
        self.root = root
        self.source = root / "2016" / "Juillet 2016"
        self.target = root / "Tri" / "2016" / "Vacances"
        self.source.mkdir(parents=True)
        self.photos = {name: os.urandom(2048) for name in ("a.jpg", "b.jpg")}
        for name, data in self.photos.items():
            (self.source / name).write_bytes(data)
            os.utime(self.source / name, ns=(MTIME, MTIME))
        self.journal = journal_file(journal_dir or root, "20260930-080000")
        self._seq = 0
        with JournalWriter.open(self.journal) as self._writer:
            for folder in (root / "Tri", root / "Tri" / "2016", self.target):
                folder.mkdir()
                self._record(ActionKind.CREATE_FOLDER, folder)
            for name in self.photos:
                self._move(name)
            self.source.rmdir()
            self._record(ActionKind.REMOVE_FOLDER, self.source)

    def _move(self, name: str) -> None:
        """Move one photo; `b.jpg` is journaled with its SHA-256 (another disk)."""
        source, target = self.source / name, self.target / name
        digest = (
            hashlib.sha256(self.photos[name]).hexdigest() if name == "b.jpg" else None
        )
        source.rename(target)
        self._record(ActionKind.MOVE, source, {"target": str(target), "sha256": digest})

    def _record(
        self,
        action: ActionKind,
        path: Path,
        extra: dict[str, object] | None = None,
    ) -> None:
        """Journal `pending` then `done` for an action already carried out."""
        self._seq += 1
        size = len(self.photos.get(path.name, b""))
        entry = JournalEntry(
            seq=self._seq,
            phase=Phase.SORT,
            status=Status.PENDING,
            action=action,
            path=str(path),
            host_path=str(path),
            size=size,
            mtime_ns=MTIME,
        ).model_copy(update=extra or {})
        self._writer.record(entry)
        self._writer.record(entry.as_done())

    def undo(self) -> Outcome:
        """Undo the run."""
        entries = read_journal(self.journal)
        with JournalWriter.open(self.journal) as journal:
            return UndoExecutor(journal, NullProgress()).run(entries)


def test_a_sort_run_is_undone_completely(tmp_path: Path) -> None:
    """Files back byte-identical with their dates, source folder back, target gone."""
    run = SortRun(tmp_path)
    outcome = run.undo()
    assert not outcome.skipped
    assert not outcome.failed
    for name, data in run.photos.items():
        assert (run.source / name).read_bytes() == data
        assert (run.source / name).stat().st_mtime_ns == MTIME
    assert not (tmp_path / "Tri").exists()
    assert run.undo().done == 0  # twice: nothing left to do


@pytest.mark.parametrize(
    ("change", "reason"),
    [("moved", "no longer at"), ("edited", "changed since")],
)
def test_a_moved_or_edited_file_is_skipped_the_rest_undone(
    tmp_path: Path, change: str, reason: str
) -> None:
    """Moved by hand or changed since the sort: left alone, and said why."""
    run = SortRun(tmp_path)
    moved = run.target / "b.jpg"
    if change == "moved":
        moved.rename(tmp_path / "b elsewhere.jpg")
    else:
        moved.write_bytes(b"edited")
    outcome = run.undo()
    skipped = [incident.path.name for incident in outcome.skipped]
    assert reason in outcome.skipped[0].reason
    # An edited file stays in the sorted folders, which are therefore kept too.
    kept = ["Vacances", "2016", "Tri"] if change == "edited" else []
    assert skipped == ["b.jpg", *kept]
    assert (run.source / "a.jpg").read_bytes() == run.photos["a.jpg"]
    assert not (run.source / "b.jpg").exists()


def test_every_action_kind_can_be_undone() -> None:
    """A new kind without its reversal fails here, not in a user's undo."""
    assert set(REVERSALS) == set(ActionKind)


def test_an_action_undo_does_not_know_changes_nothing(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refused before the first change: no empty file is made up."""
    run = SortRun(tmp_path)
    without_moves = {
        kind: reversal
        for kind, reversal in REVERSALS.items()
        if kind is not ActionKind.MOVE
    }
    monkeypatch.setattr(
        "media_hygiene.actions.reversal.REVERSALS", MappingProxyType(without_moves)
    )
    with pytest.raises(JournalError, match="cannot undo"):
        run.undo()
    assert not run.source.exists()
    assert sorted(path.name for path in run.target.iterdir()) == ["a.jpg", "b.jpg"]


def test_history_names_the_command_of_each_run(
    cli: CliRunner, locations: Locations, tmp_path: Path
) -> None:
    """A sort run says `sort`, with the files it moved."""
    SortRun(tmp_path / "photos", locations.journal_dir)
    history = run(cli, "history").output
    assert " sort " in history
    assert "Moved" in history


def test_a_run_without_a_plan_is_undone_alone(tmp_path: Path) -> None:
    """No plan id in its journal (nothing to walk back through): the run alone."""
    sort_run = SortRun(tmp_path)
    plan = runs_of_plan(tmp_path, sort_run.journal.stem)
    assert [each.run_id for each in plan.runs] == [sort_run.journal.stem]
    assert plan.runs[0].moved == len(sort_run.photos)
    assert not plan.together
    assert plan.later is None
