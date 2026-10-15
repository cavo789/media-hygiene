"""A few groups of a sort move at once (0163): names, counters, Ctrl+C, resume, undo."""

from __future__ import annotations

import os
import threading
import time
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalWriter, journal_file, read_journal
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.no_overwrite import rename_no_replace
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.parallel import WORKERS
from media_hygiene.actions.sort import SortExecutor
from media_hygiene.actions.sort_moves import SortContext
from media_hygiene.actions.sort_plan import Move, MoveGroup, SortPlan
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.classify.models import Band
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    import pytest

    from media_hygiene.actions.sort import MoveOutcome

MTIME = 1_600_000_000_000_000_000
GROUPS = 12
PAUSE = 0.02  # seconds each move takes, so that the workers overlap


def write(path: Path, data: bytes) -> Path:
    """Write a file with a fixed modification time."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.utime(path, ns=(MTIME, MTIME))
    return path


def group_of(tmp_path: Path, index: int, target: Path) -> MoveGroup:
    """A photo and its RAW twin, from their own folder, both named `IMG_1`."""
    paths = [
        write(tmp_path / "src" / f"{index:02}" / name, f"{index}{name}".encode())
        for name in ("IMG_1.jpg", "IMG_1.CR2")
    ]
    moves = tuple(
        Move(path.name, path, path.stat().st_size, MTIME, Band.SURE) for path in paths
    )
    return MoveGroup(tmp_path, target, moves)


def run(
    tmp_path: Path, plan: SortPlan, stop: Callable[[], bool] = lambda: False
) -> MoveOutcome:
    """Execute a plan into the journal `run-<n>` of `tmp_path`."""
    run_id = f"run-{len(list(tmp_path.glob('run-*')))}"
    with JournalWriter.open(journal_file(tmp_path, run_id)) as writer:
        changes = CleanContext(
            writer, HostPathMapper(tmp_path), tmp_path / "q", NullProgress(), Phase.SORT
        )
        return SortExecutor(SortContext(changes, "plan", stop), Tally()).run(plan)


def undo_all(tmp_path: Path) -> None:
    """Undo every run, newest first."""
    for journal in sorted(tmp_path.glob("run-*"), reverse=True):
        with JournalWriter.open(journal) as writer:
            outcome = UndoExecutor(writer, NullProgress()).run(read_journal(journal))
        assert not outcome.failed


class Overlap:
    """A slow rename that counts the moves under way at once."""

    def __init__(self, after: Callable[[], None] = lambda: None) -> None:
        """Start with no move under way; `after` runs after each move."""
        self.lock = threading.Lock()
        self.now = 0
        self.peak = 0
        self.after = after

    def __call__(self, source: Path, target: Path) -> None:
        """Rename, slowly."""
        with self.lock:
            self.now += 1
            self.peak = max(self.peak, self.now)
        time.sleep(PAUSE)
        rename_no_replace(source, target)
        with self.lock:
            self.now -= 1
        self.after()


def snapshot(root: Path) -> dict[str, bytes]:
    """Every file under `root`, by relative path, with its bytes."""
    return {
        str(path.relative_to(root)): path.read_bytes()
        for path in root.rglob("*")
        if path.is_file()
    }


def test_a_few_moves_at_once_names_decided_first(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Twelve `IMG_1` pairs into one folder: four at most at once, each its suffix."""
    target = tmp_path / "t"
    plan = SortPlan("plan", tuple(group_of(tmp_path, i, target) for i in range(GROUPS)))
    start = snapshot(tmp_path / "src")
    overlap = Overlap()
    monkeypatch.setattr("media_hygiene.actions.sort_moves.rename_no_replace", overlap)
    outcome = run(tmp_path, plan)
    assert 1 < overlap.peak <= WORKERS
    assert not outcome.outcome.failed
    assert not outcome.outcome.skipped
    assert outcome.outcome.done == 2 * GROUPS  # the counters, under a lock
    assert outcome.outcome.bytes_done == sum(len(data) for data in start.values())
    for index in range(GROUPS):  # the names follow the plan's order, pair by pair
        suffix = "" if index == 0 else f" ({index + 1})"
        for ext in ("jpg", "CR2"):
            moved = (target / f"IMG_1{suffix}.{ext}").read_bytes()
            assert moved == f"{index}IMG_1.{ext}".encode()
    seqs = [entry.seq for entry in outcome.moved]
    assert seqs == sorted(seqs)  # the manifest's order, whatever ended first
    folders = [
        entry
        for entry in read_journal(journal_file(tmp_path, "run-0"))
        if entry.action is ActionKind.CREATE_FOLDER and entry.status is Status.DONE
    ]
    assert [entry.path for entry in folders] == [str(target)]  # made once
    undo_all(tmp_path)
    assert snapshot(tmp_path / "src") == start
    assert not target.exists()


def test_ctrl_c_ends_the_groups_under_way_and_a_new_run_resumes(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Stopped after the first move: no pair is split, the rest moves next run."""
    target = tmp_path / "t"
    groups = tuple(group_of(tmp_path, i, target) for i in range(GROUPS))
    start = snapshot(tmp_path / "src")
    asked = threading.Event()
    monkeypatch.setattr(
        "media_hygiene.actions.sort_moves.rename_no_replace", Overlap(asked.set)
    )
    first = run(tmp_path, SortPlan("plan", groups), asked.is_set)
    assert first.interrupted
    assert 0 < first.outcome.done < 2 * GROUPS
    journal = read_journal(journal_file(tmp_path, "run-0"))
    pending = {entry.seq for entry in journal if entry.status is Status.PENDING}
    assert pending == {entry.seq for entry in journal if entry.status is Status.DONE}
    left = tuple(group for group in groups if group.moves[0].source.exists())
    assert all(move.source.exists() for group in left for move in group.moves)
    second = run(tmp_path, SortPlan("plan", left))
    assert not second.interrupted
    assert first.outcome.done + second.outcome.done == 2 * GROUPS
    assert len(list(target.iterdir())) == 2 * GROUPS
    undo_all(tmp_path)
    assert snapshot(tmp_path / "src") == start
    assert not target.exists()
