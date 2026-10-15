"""The small parts of `sort`: names, stop requests, the proof, the closing summary."""

from __future__ import annotations

import os
import signal
from dataclasses import replace
from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene.actions.journal import JournalEntry
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.manifest import Census, Manifest, census, verify_moves
from media_hygiene.actions.outcome import Incident, Outcome
from media_hygiene.actions.sort import MoveOutcome
from media_hygiene.actions.sort_folders import Fate, FolderReport, Verdict
from media_hygiene.actions.sort_names import numbered
from media_hygiene.cli.cmd_sort import _show_result
from media_hygiene.console.advice import TipKind
from media_hygiene.errors import MountError
from media_hygiene.scan.stopwatch import Stage, StageTime
from media_hygiene.services.interrupt import StopRequest
from media_hygiene.services.sort_models import SortResult
from media_hygiene.services.sort_report import write_manifest
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def entry(path: Path, target: Path, sha256: str | None = None) -> JournalEntry:
    """A move of a 4-byte file."""
    return JournalEntry(
        seq=1,
        phase=Phase.SORT,
        status=Status.DONE,
        action=ActionKind.MOVE,
        path=str(path),
        host_path=str(path),
        size=4,
        mtime_ns=0,
        target=str(target),
        sha256=sha256,
    )


def test_numbered_names_keep_their_group_together() -> None:
    """The suffix follows the common name; a stranger name gets it before its end."""
    assert numbered("IMG_1.CR2.xmp", "IMG_1", 2) == "IMG_1 (2).CR2.xmp"
    assert numbered("other.jpg", "IMG_1", 3) == "other (3).jpg"
    assert numbered("IMG_1.jpg", "IMG_1", 1) == "IMG_1.jpg"


def test_ctrl_c_becomes_a_request() -> None:
    """Inside the block, SIGINT is recorded; outside, the usual handler is back."""
    before = signal.getsignal(signal.SIGINT)
    with StopRequest() as stop:
        assert not stop.requested()
        os.kill(os.getpid(), signal.SIGINT)
        assert stop.requested()
    assert signal.getsignal(signal.SIGINT) is before


def test_the_census_counts_each_file_once_junk_apart(tmp_path: Path) -> None:
    """Nested roots count once; Thumbs.db and symbolic links are not counted."""
    (tmp_path / "a" / "b").mkdir(parents=True)
    (tmp_path / "a" / "b" / "x.jpg").write_bytes(b"1234")
    (tmp_path / "a" / "Thumbs.db").write_bytes(b"junk")
    (tmp_path / "a" / "link.jpg").symlink_to(tmp_path / "a" / "b" / "x.jpg")
    found = census([tmp_path / "a" / "b", tmp_path / "a"], frozenset({"thumbs.db"}))
    assert found == Census(files=1, bytes=4)


def test_every_move_is_checked(tmp_path: Path) -> None:
    """Missing, resized or altered at its target: each is a problem."""
    whole = tmp_path / "whole.jpg"
    whole.write_bytes(b"1234")
    resized = tmp_path / "resized.jpg"
    resized.write_bytes(b"12")
    altered = tmp_path / "altered.jpg"
    altered.write_bytes(b"abcd")
    moves = [
        entry(tmp_path / "s1", whole),
        entry(tmp_path / "s2", tmp_path / "gone.jpg"),
        entry(tmp_path / "s3", resized),
        entry(tmp_path / "s4", altered, sha256="0" * 64),
    ]
    verified, problems = verify_moves(moves, str)
    assert verified == 1
    assert [problem.split(": ")[1] for problem in problems] == [
        f"the file moved from {tmp_path / 's2'} is not there",
        "its size changed",
        "its content changed",
    ]


def manifest(*problems: str) -> Manifest:
    """The proof of a run."""
    return Manifest(
        run_id="20260930-100000",
        plan_id="plan",
        roots=("C:\\",),
        before=Census(files=2, bytes=8),
        after=Census(files=1 if problems else 2, bytes=4 if problems else 8),
        moved=2,
        verified=1 if problems else 2,
        problems=problems,
    )


def test_an_unwritable_manifest_is_a_mount_error(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The moves are over: the service turns it into a warning."""

    def denied(_self: Path, *_args: object, **_kwargs: object) -> None:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(Path, "mkdir", denied)
    runtime = make_runtime(locations)
    with pytest.raises(MountError) as raised:
        write_manifest(runtime, manifest())
    assert "--user" in (raised.value.tip or "")


def test_the_closing_summary_tells_what_went_wrong(locations: Locations) -> None:
    """Skipped, failed, stopped, not proven, manifest not written: all said."""
    runtime = make_runtime(locations)
    path = locations.data_dir / "c" / "a.jpg"
    outcome = Outcome(
        1, 4, 0, (Incident(path, "changed"),), (Incident(path, "denied"),)
    )
    kept = (Verdict(locations.data_dir / "c" / "old", Fate.HOLDS_FILES),)
    result = SortResult(
        "20260930-100000",
        MoveOutcome(outcome, (), interrupted=True),
        FolderReport(1, kept),
        manifest("C:\\b.jpg: its size changed"),
        MountError("The manifest could not be written."),
    )
    _show_result(runtime, result)
    text = " ".join(output_of(runtime).split())
    assert "Time per step" not in text  # only with --verbosity verbose
    for expected in (
        "C:\\a.jpg: changed",
        "C:\\a.jpg: denied",
        "Source folders removed: 1.",
        "1 source folder stays",
        "Check this run: 2 files",
        "its size changed",
        "could not be written",
        "Run the same command again",
    ):
        assert expected in text, expected
    step, tips, _settings = runtime.output.board.drain()
    assert step is None
    (undo,) = tips
    assert undo.kind is TipKind.SAFETY
    assert undo.command is not None
    assert undo.command.endswith("undo 20260930-100000")


def reference_census(roots: list[Path], junk: frozenset[str]) -> Census:
    """The census before 0170 (os.walk, three stats per file), kept as the reference."""
    outer = [
        root
        for root in sorted(set(roots), key=lambda root: len(root.parts))
        if not any(root != other and root.is_relative_to(other) for other in roots)
    ]
    files = size = 0
    for root in outer:
        for folder, _dirs, names in os.walk(root):
            for name in names:
                path = Path(folder, name)
                if name.casefold() in junk or path.is_symlink() or not path.is_file():
                    continue
                files += 1
                size += path.stat().st_size
    return Census(files=files, bytes=size)


def test_the_census_counts_what_it_counted_before(tmp_path: Path) -> None:
    """Links to files and folders, a pipe, junk in any case, no root: as before."""
    root = tmp_path / "root"
    (root / "a" / "deep").mkdir(parents=True)
    (root / "a" / "deep" / "x.jpg").write_bytes(b"12345")
    (root / "b.jpg").write_bytes(b"12")
    (root / "a" / "THUMBS.DB").write_bytes(b"junk")
    (root / "a" / "to-file.jpg").symlink_to(root / "b.jpg")
    (root / "to-folder").symlink_to(root / "a", target_is_directory=True)
    (root / "broken.jpg").symlink_to(tmp_path / "nowhere")
    os.mkfifo(root / "pipe")
    elsewhere = tmp_path / "elsewhere"
    elsewhere.mkdir()
    (elsewhere / "y.jpg").write_bytes(b"1")
    roots = [root, root / "a", elsewhere, tmp_path / "missing"]
    junk = frozenset({"thumbs.db"})
    assert census(roots, junk) == reference_census(roots, junk)
    assert census(roots, junk) == Census(files=3, bytes=8)


def test_the_census_reads_each_file_with_one_stat(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Neither `os.stat` nor `os.lstat` per file: the listing's entry gives the size."""
    for index in range(5):
        (tmp_path / f"{index}.jpg").write_bytes(b"1234")
    calls: list[str] = []
    real_stat, real_lstat = os.stat, os.lstat

    def counted_stat(*args: object, **kwargs: object) -> os.stat_result:
        calls.append("stat")
        return real_stat(*args, **kwargs)  # type: ignore[arg-type]

    def counted_lstat(*args: object, **kwargs: object) -> os.stat_result:
        calls.append("lstat")
        return real_lstat(*args, **kwargs)  # type: ignore[arg-type]

    monkeypatch.setattr(os, "stat", counted_stat)
    monkeypatch.setattr(os, "lstat", counted_lstat)
    assert census([tmp_path], frozenset()) == Census(files=5, bytes=20)
    assert not calls


def test_a_folder_at_the_target_is_not_the_file_moved(tmp_path: Path) -> None:
    """One `stat` still tells a file from a folder of the same name."""
    (tmp_path / "folder.jpg").mkdir()
    verified, problems = verify_moves(
        [entry(tmp_path / "s", tmp_path / "folder.jpg")], str
    )
    assert verified == 0
    assert "is not there" in problems[0]


def test_a_verbose_sort_says_where_its_time_went(locations: Locations) -> None:
    """`--verbosity verbose`: one line, each stage and its time (0170)."""
    runtime = make_runtime(locations)
    runtime = replace(runtime, output=replace(runtime.output, verbose=True))
    result = SortResult(
        "20260930-100000",
        MoveOutcome(Outcome(2, 8, 0, (), ()), (), interrupted=False),
        FolderReport(),
        manifest(),
        None,
        (StageTime(Stage.COUNTS, 0.25), StageTime(Stage.MOVES, 70.0)),
    )
    _show_result(runtime, result)
    text = " ".join(output_of(runtime).split())
    assert "Time per step: counts 0.2 s · moves 1 min 10 s" in text
