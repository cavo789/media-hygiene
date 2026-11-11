"""0690: the slow re-read finds a silently damaged file; `clean --repair` restores it.

One test per event that changes what the index trusts: a byte flipped keeping size
and date (damage), an edit (new date), a `touch`, a rewrite keeping the date (listed
as changed or damaged), a move by the tool, a file forgotten, an older index file.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from types import SimpleNamespace
from typing import TYPE_CHECKING, Any

from typer.testing import CliRunner

from media_hygiene.actions.journal import JournalEntry, JournalWriter, journal_file
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.cli.app import build_app
from media_hygiene.config.settings import Settings
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.schema import SCHEMA_VERSION
from media_hygiene.index.verified_rows import damaged_files
from media_hygiene.paths.mounts import MountTable
from media_hygiene.plan.push_entries import Stat
from media_hygiene.scan.hashing import full_digest
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.good_copy import CopyPlace, repairables
from media_hygiene.services.push_broken import BrokenFinder
from media_hygiene.services.repair import jobs_of, repair
from media_hygiene.services.reread import reread
from media_hygiene.services.undo import undo_run
from media_hygiene.services.upkeep import commands_of
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime


def _library(locations: Locations) -> tuple[Runtime, Path, Path]:
    """Two identical photos and one alone, audited; the runtime and the pair."""
    photos = locations.data_dir / "c" / "Photos"
    (photos / "a").mkdir(parents=True)
    (photos / "b").mkdir(parents=True)
    first = photos / "a" / "IMG_0001.jpg"
    scene(1).save(first, quality=90)
    twin = photos / "b" / "IMG_0001.jpg"
    shutil.copy2(first, twin)
    scene(2).save(photos / "a" / "IMG_0002.jpg", quality=90)
    runtime = replace(
        make_runtime(locations), mounts=MountTable(frozenset({photos}), (), ())
    )
    _audit(runtime)
    return runtime, first, twin


def _audit(runtime: Runtime) -> None:
    """An incremental audit."""
    AuditService(runtime, NullProgress()).run()


def _flip(path: Path, offset: int | None = None) -> None:
    """Flip one byte in the middle, keeping size and modification time."""
    stat = path.stat()
    data = bytearray(path.read_bytes())
    data[len(data) // 2 if offset is None else offset] ^= 0xFF
    path.write_bytes(bytes(data))
    os.utime(path, ns=(stat.st_atime_ns, stat.st_mtime_ns))


def _damaged(runtime: Runtime) -> list[str]:
    """The paths the index holds as damaged."""
    assert runtime.index_file is not None
    with FactsRepository.open(runtime.index_file) as repository:
        return [row.path for row in damaged_files(repository.connection)]


def test_a_flipped_byte_is_found_listed_restored_and_undone(
    locations: Locations,
) -> None:
    """Acceptance: found by the re-read, its copy named, disk identical, undoable."""
    runtime, first, twin = _library(locations)
    assert reread(runtime).files == 3
    before, mtime = first.read_bytes(), first.stat().st_mtime_ns
    _flip(first)
    _audit(runtime)  # size and date unchanged: the audit trusts it
    result = reread(runtime)
    assert result.damaged == (str(first),)
    found = repairables(runtime)
    assert [(item.copy, item.place) for item in found] == [(twin, CopyPlace.LIBRARY)]
    outcome = repair(runtime, jobs_of(found), NullProgress())
    assert outcome.proven == (first,)
    assert first.read_bytes() == before
    assert first.stat().st_mtime_ns == mtime
    assert not _damaged(runtime)
    quarantined = list(locations.quarantine_dir.rglob("IMG_0001.jpg"))
    assert len(quarantined) == 1
    assert quarantined[0].read_bytes() != before
    undo_run(runtime, outcome.run_id, NullProgress())
    assert first.read_bytes() != before  # the damaged file is back, as it was
    assert first.stat().st_size == len(before)


def test_a_first_reading_compares_with_the_audit_digest(locations: Locations) -> None:
    """A file with a copy has its full digest from the audit: damage found at once."""
    runtime, first, _twin = _library(locations)
    _flip(first)
    assert reread(runtime).damaged == (str(first),)


def test_a_first_reading_compares_the_ends_without_a_full_digest(
    locations: Locations,
) -> None:
    """A file alone: its first 64 KiB changed, listed, no copy to prove."""
    runtime, _first, _twin = _library(locations)
    alone = locations.data_dir / "c" / "Photos" / "a" / "IMG_0002.jpg"
    _flip(alone, 10)
    assert reread(runtime).damaged == (str(alone),)
    assert [item.copy for item in repairables(runtime)] == [None]
    assert not jobs_of(repairables(runtime))


def test_an_edit_with_a_new_date_is_never_damage(locations: Locations) -> None:
    """Changed then audited: a new start, not damage."""
    runtime, first, _twin = _library(locations)
    reread(runtime)
    scene(5).save(first, quality=80)
    assert reread(runtime).files == 2  # left to the audit: it changed since
    _audit(runtime)
    assert not reread(runtime).damaged
    assert not _damaged(runtime)


def test_a_touch_is_a_new_start(locations: Locations) -> None:
    """Same bytes, a new date: read fine once audited."""
    runtime, first, _twin = _library(locations)
    reread(runtime)
    first.touch()
    _audit(runtime)
    assert not reread(runtime).damaged


def test_a_rewrite_keeping_the_date_is_listed_as_changed(locations: Locations) -> None:
    """`touch -r` after an EXIF rewrite: listed (changed or damaged — look)."""
    runtime, first, _twin = _library(locations)
    reread(runtime)
    stat = first.stat()
    data = first.read_bytes()
    first.write_bytes(data[:-3] + b"XYZ")
    os.utime(first, ns=(stat.st_atime_ns, stat.st_mtime_ns))
    assert reread(runtime).damaged == (str(first),)


def test_the_budget_reads_the_oldest_first(locations: Locations) -> None:
    """One byte of budget: one file per run, the never read first, then in turn."""
    runtime, _first, _twin = _library(locations)
    seen = [reread(runtime, 1).files for _ in range(3)]
    assert seen == [1, 1, 1]
    assert reread(runtime, 0).files == 0
    assert runtime.index_file is not None
    with FactsRepository.open(runtime.index_file) as repository:
        count = repository.connection.execute("SELECT COUNT(*) FROM verified")
        assert count.fetchone() == (3,)


def test_a_move_by_the_tool_and_a_forget_follow_the_row(locations: Locations) -> None:
    """`sort`/`undo` move the row; the audit forgetting a file drops it."""
    runtime, first, _twin = _library(locations)
    reread(runtime)
    _flip(first)
    reread(runtime)
    assert runtime.index_file is not None
    moved = str(first.with_name("moved.jpg"))
    with FactsRepository.open(runtime.index_file) as repository:
        repository.move([(str(first), moved)])
    assert _damaged(runtime) == [moved]
    with FactsRepository.open(runtime.index_file) as repository:
        repository.forget([moved])
    assert not _damaged(runtime)


def test_a_good_copy_in_the_quarantine_is_found(locations: Locations) -> None:
    """The twin set aside before: its journal's SHA-256 names it."""
    runtime, first, twin = _library(locations)
    reread(runtime)
    aside = locations.quarantine_dir / "run1" / "IMG_0001.jpg"
    aside.parent.mkdir(parents=True)
    shutil.move(twin, aside)
    with JournalWriter.open(journal_file(locations.journal_dir, "run1")) as journal:
        fields = {
            "action": ActionKind.QUARANTINE_DUPLICATE,
            "phase": Phase.CLEAN,
            "status": Status.DONE,
            "seq": 1,
            "path": str(twin),
            "host_path": "C:\\x",
            "size": aside.stat().st_size,
            "mtime_ns": aside.stat().st_mtime_ns,
            "sha256": full_digest(aside),
            "quarantine": str(aside),
        }
        journal.record(JournalEntry.model_validate(fields))
    _flip(first)
    reread(runtime)
    found = repairables(runtime)
    assert [(item.copy, item.place) for item in found] == [
        (aside, CopyPlace.QUARANTINE)
    ]


def test_push_never_replaces_a_copy_by_a_damaged_file(locations: Locations) -> None:
    """The damaged file, unchanged since, is refused like a broken one."""
    runtime, first, _twin = _library(locations)
    _flip(first)
    reread(runtime)
    stat = first.stat()
    check: Any = SimpleNamespace(pc_path=lambda relative: first.parent / relative)
    finder = BrokenFinder(runtime, check)
    files = {first.name: Stat(stat.st_size, stat.st_mtime_ns)}
    assert finder.broken(files) == frozenset({first.name})


def test_an_index_of_version_19_gains_the_table_in_place(tmp_path: Path) -> None:
    """The rows stay; the new table is created once."""
    index = tmp_path / "index.sqlite"
    with FactsRepository.open(index) as repository:
        repository.connection.execute(
            "INSERT INTO files (path, size, mtime_ns) VALUES ('/x', 1, 2)"
        )
        repository.connection.execute("DROP TABLE verified")
        repository.connection.execute("PRAGMA user_version = 19")
    with FactsRepository.open(index) as repository:
        connection = repository.connection
        assert connection.execute("PRAGMA user_version").fetchone() == (SCHEMA_VERSION,)
        assert connection.execute("SELECT COUNT(*) FROM verified").fetchone() == (0,)
        assert connection.execute("SELECT path FROM files").fetchall() == [("/x",)]


def test_the_upkeep_step_runs_the_reread() -> None:
    """`[routine] steps` has `reread` by default: `audit --reread`."""
    routine = Settings().routine
    assert routine.reread_gb > 0
    runtime: Any = None
    assert commands_of(runtime, routine.steps[-1]) == (("audit", "--reread"),)


def test_the_console_lists_first_then_restores(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`audit --reread` lists the file and its copy; `clean --repair --yes` restores."""
    point_mounts(locations, monkeypatch)
    _runtime, first, _twin = _library(locations)
    before = first.read_bytes()
    _flip(first)
    listed = run(CliRunner(), "audit", "--reread")
    assert listed.exit_code == 0, listed.output
    assert "IMG_0001.jpg" in listed.output
    assert "mh clean --repair" in listed.output
    declined = CliRunner().invoke(build_app(), ["clean", "--repair"], input="n\n")
    assert declined.exit_code == 0, declined.output
    assert first.read_bytes() != before
    restored = run(CliRunner(), "clean", "--repair", "--yes")
    assert restored.exit_code == 0, restored.output
    assert first.read_bytes() == before
    assert "mh undo" in restored.output
