"""One move at a time: a name taken, another disk, a changed file, companions."""

from __future__ import annotations

import errno
import os
from typing import TYPE_CHECKING

from media_hygiene.actions.journal import JournalWriter, journal_file, read_journal
from media_hygiene.actions.journaled import CleanContext
from media_hygiene.actions.kinds import Phase
from media_hygiene.actions.outcome import Tally
from media_hygiene.actions.sort import SortExecutor
from media_hygiene.actions.sort_moves import SortContext
from media_hygiene.actions.sort_plan import Move, MoveGroup, SortPlan
from media_hygiene.actions.undo import UndoExecutor
from media_hygiene.classify.models import Band
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.progress import NullProgress

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.actions.sort import MoveOutcome

MTIME = 1_600_000_000_000_000_000


def write(path: Path, data: bytes) -> Path:
    """Write a file with a fixed modification time."""
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_bytes(data)
    os.utime(path, ns=(MTIME, MTIME))
    return path


def move_of(path: Path) -> Move:
    """The move of a file as `classify` saw it."""
    return Move(path.name, path, path.stat().st_size, MTIME, Band.SURE)


def run(tmp_path: Path, groups: tuple[MoveGroup, ...]) -> MoveOutcome:
    """Execute groups of moves with a journal in `tmp_path`, then check undo."""
    journal = journal_file(tmp_path, "run")
    with JournalWriter.open(journal) as writer:
        changes = CleanContext(
            writer, HostPathMapper(tmp_path), tmp_path / "q", NullProgress(), Phase.SORT
        )
        context = SortContext(changes, "plan", lambda: False)
        return SortExecutor(context, Tally()).run(SortPlan("plan", groups))


def undo(tmp_path: Path) -> None:
    """Undo the run."""
    journal = journal_file(tmp_path, "run")
    with JournalWriter.open(journal) as writer:
        outcome = UndoExecutor(writer, NullProgress()).run(read_journal(journal))
    assert not outcome.failed
    assert not outcome.skipped


def test_a_name_taken_gets_a_suffix_and_nothing_is_overwritten(tmp_path: Path) -> None:
    """The target already holds an `IMG_1.jpg`: ours becomes `IMG_1 (2).jpg`."""
    source = write(tmp_path / "a" / "IMG_1.jpg", b"ours")
    taken = write(tmp_path / "t" / "IMG_1.jpg", b"theirs")
    group = MoveGroup(tmp_path, tmp_path / "t", (move_of(source),))
    outcome = run(tmp_path, (group,))
    assert outcome.outcome.done == 1
    assert taken.read_bytes() == b"theirs"
    assert (tmp_path / "t" / "IMG_1 (2).jpg").read_bytes() == b"ours"
    undo(tmp_path)
    assert source.read_bytes() == b"ours"


def test_another_disk_copies_verifies_and_journals_the_digest(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rename refused across disks: copied, proven, SHA-256 in the journal."""
    source = write(tmp_path / "a" / "IMG_1.jpg", b"photo")

    def cross(_source: Path, target: Path) -> None:
        raise OSError(errno.EXDEV, "Invalid cross-device link", str(target))

    monkeypatch.setattr("media_hygiene.actions.sort_moves.rename_no_replace", cross)
    group = MoveGroup(tmp_path, tmp_path / "t", (move_of(source),))
    outcome = run(tmp_path, (group,))
    assert not outcome.outcome.failed
    assert outcome.moved[0].sha256
    assert not source.exists()
    assert (tmp_path / "t" / "IMG_1.jpg").stat().st_mtime_ns == MTIME
    undo(tmp_path)
    assert source.read_bytes() == b"photo"


def test_a_changed_file_is_skipped_with_its_sidecar(tmp_path: Path) -> None:
    """Edited since `classify`: it stays, and so does its sidecar."""
    source = write(tmp_path / "a" / "IMG_1.jpg", b"photo")
    move = move_of(source)
    write(source, b"edited since")
    sidecar = write(tmp_path / "a" / "IMG_1.xmp", b"<xmp/>")
    outcome = run(tmp_path, (MoveGroup(tmp_path, tmp_path / "t", (move,)),))
    assert "changed" in outcome.outcome.skipped[0].reason
    assert source.exists()
    assert sidecar.exists()
    assert not (tmp_path / "t").exists()  # no folder made for nothing


def test_companions_travel_together_with_one_suffix(tmp_path: Path) -> None:
    """Live Photo, RAW twin and sidecars: one folder, the same ` (2)`."""
    folder = tmp_path / "a"
    files = [
        write(folder / name, name.encode()) for name in ("IMG_1.HEIC", "IMG_1.MOV")
    ]
    files += [write(folder / name, name.encode()) for name in ("IMG_1.CR2",)]
    sidecars = [write(folder / name, b"x") for name in ("IMG_1.xmp", "IMG_1.CR2.xmp")]
    write(tmp_path / "t" / "IMG_1.MOV", b"someone else's")
    moves = tuple(move_of(path) for path in files)
    outcome = run(tmp_path, (MoveGroup(tmp_path, tmp_path / "t", moves),))
    assert outcome.outcome.done == len(files) + len(sidecars)
    names = sorted(path.name for path in (tmp_path / "t").iterdir())
    assert names == [
        "IMG_1 (2).CR2",
        "IMG_1 (2).CR2.xmp",
        "IMG_1 (2).HEIC",
        "IMG_1 (2).MOV",
        "IMG_1 (2).xmp",
        "IMG_1.MOV",
    ]
    assert not list(folder.iterdir())
    undo(tmp_path)
    assert sorted(path.name for path in folder.iterdir()) == sorted(
        path.name for path in (*files, *sidecars)
    )
