"""`mh push` (0264): planned by the container, applied by a stand-in, proven.

The stand-in does what `mh_push.ps1.j2` does: the renames of the plan, then a
robocopy of each photo folder (every file new or changed by size and date, never a
broken one, nothing deleted). The closing run proves it; a second run plans nothing; a
move on the PC is a rename on the backup; `mh push --undo` puts back what a run set
aside; the photos are never written.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.actions.journal import (
    JournalEntry,
    JournalWriter,
    journal_file,
    read_journal,
)
from media_hygiene.actions.kinds import ActionKind, Phase, Status
from media_hygiene.actions.runs import summarize
from media_hygiene.errors import JournalError, MountError
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mounts import MountTable
from media_hygiene.plan.backup_gone import GoneReason
from media_hygiene.plan.push_entries import Stat
from media_hygiene.services.push_journal import push_run, record_pending
from media_hygiene.services.push_lines import plan_lines
from media_hygiene.services.push_place import REMOVED_FOLDER
from media_hygiene.services.push_proof import ProofQuery, plan_of, prove_push
from media_hygiene.services.push_run import prepare_push
from media_hygiene.services.push_sources import push_target
from media_hygiene.services.push_undo import plan_undo, record_undone
from media_hygiene.services.undo_guard import ensure_undo_ready
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.push_proof import PushProof
    from media_hygiene.services.runtime import Runtime

TARGET: Final = "E:\\Backup"
PHOTOS: Final = "c/Family Photos"


def mounted(locations: Locations, *more: str) -> Runtime:
    """The demo's photo folder and the target mounted apart, as `mh push` does."""
    data = locations.data_dir
    (data / "e" / "Backup").mkdir(parents=True, exist_ok=True)
    folders = frozenset(
        {data / PHOTOS, data / "e" / "Backup", *(data / m for m in more)}
    )
    return replace(make_runtime(locations), mounts=MountTable(folders, (), ()))


def photos_of(locations: Locations) -> dict[str, tuple[int, int]]:
    """Every photo file's size and time, to prove they are never written."""
    root = locations.data_dir / PHOTOS
    return {
        str(path): (path.stat().st_size, path.stat().st_mtime_ns)
        for path in root.rglob("*")
        if path.is_file()
    }


def windows(runtime: Runtime, lines: list[str]) -> None:
    """The stand-in for `mh_push.ps1.j2`: renames, then robocopy, never a deletion."""
    target = push_target(runtime, TARGET)
    plan = plan_of(runtime, ProofQuery(TARGET, lines))
    record_pending(
        push_run(runtime.locations.journal_dir, plan.run_id, target), plan.changes
    )
    for change in plan.changes:
        old, new = target.point / change.old.path, target.point / change.new
        if old.exists() and not new.exists():
            new.parent.mkdir(parents=True, exist_ok=True)
            old.rename(new)
    broken = {line.split("\t")[1] for line in lines if line.startswith("broken\t")}
    for line in lines:
        fields = line.split("\t")
        if fields[0] == "source":
            robocopy(runtime, (fields[1], fields[2]), broken)


def robocopy(runtime: Runtime, folders: tuple[str, str], broken: set[str]) -> None:
    """Copy every file new or changed by size and date, keeping its date."""
    source = runtime.mapper.to_container(folders[0])
    target = push_target(runtime, TARGET)
    into = target.point / (target.relative(folders[1]) or "")
    for path in source.rglob("*"):
        if not path.is_file() or runtime.mapper.to_host(path) in broken:
            continue
        copy = into / path.relative_to(source)
        stat = path.stat()
        there = copy.stat() if copy.is_file() else None
        if there and Stat(there.st_size, there.st_mtime_ns).same(
            Stat(stat.st_size, stat.st_mtime_ns)
        ):
            continue
        copy.parent.mkdir(parents=True, exist_ok=True)
        shutil.copy2(path, copy)


def backed_up(runtime: Runtime) -> tuple[list[str], PushProof]:
    """One whole run: plan, applied, proven; its lines and its proof."""
    lines = list(plan_lines(prepare_push(runtime, TARGET, anyway=False)))
    windows(runtime, lines)
    return lines, prove_push(runtime, ProofQuery(TARGET, lines, 1.0))


def journal_clean(runtime: Runtime, path: Path, action: ActionKind) -> None:
    """A run of `clean` that removed a file, its quarantine since purged."""
    journal_dir = runtime.locations.journal_dir
    stat = path.stat()
    entry = JournalEntry(
        seq=1,
        phase=Phase.CLEAN,
        status=Status.DONE,
        action=action,
        path=str(path),
        host_path=runtime.mapper.to_host(path),
        size=stat.st_size,
        mtime_ns=stat.st_mtime_ns,
    )
    with JournalWriter.open(journal_file(journal_dir, "20260101-120000")) as journal:
        journal.record(entry)


def test_a_first_backup_copies_everything_and_proves_it(locations: Locations) -> None:
    """Each file below `<target>/C/Family Photos`, same bytes and date; journaled."""
    build_demo(locations.data_dir)
    before = photos_of(locations)
    runtime = mounted(locations)
    _lines, proof = backed_up(runtime)
    photos = locations.data_dir / PHOTOS
    copy = locations.data_dir / "e/Backup/C/Family Photos/2019/Vacances/IMG_0001.jpg"
    assert copy.read_bytes() == (photos / "2019/Vacances/IMG_0001.jpg").read_bytes()
    assert proof.copied == len(before)
    assert not proof.missing
    assert not proof.failed
    assert proof.held == len(before)
    assert photos_of(locations) == before
    summary = summarize(runtime.locations.journal_dir, proof.run_id)
    assert summary.kind is Phase.PUSH
    assert summary.kept.copied == proof.copied_bytes > 0


def test_a_second_run_plans_nothing(locations: Locations) -> None:
    """Everything is there: nothing to copy, rename or set aside."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    plan = prepare_push(runtime, TARGET, anyway=False).plan
    assert not plan.copies
    assert not plan.moves
    assert not plan.gone
    assert plan.unchanged == plan.held


def test_a_folder_renamed_on_the_pc_is_renamed_on_the_backup(
    locations: Locations,
) -> None:
    """A sort, or a rename in the Explorer: renames on the backup, nothing sent."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    photos = locations.data_dir / PHOTOS
    (photos / "2019").rename(photos / "2019 - Holidays")
    files = sum(path.is_file() for path in (photos / "2019 - Holidays").rglob("*"))
    prepared = prepare_push(runtime, TARGET, anyway=False)
    assert not prepared.plan.copies
    assert len(prepared.plan.moves) == files == 5  # three photos, a twin, a sidecar
    _lines, proof = backed_up(runtime)
    assert proof.renamed == files
    assert proof.copied == 0
    assert not proof.missing
    old = locations.data_dir / "e/Backup/C/Family Photos/2019"
    assert not any(old.rglob("*.jpg"))
    assert summarize(runtime.locations.journal_dir, proof.run_id).moved == files


def test_identical_twins_are_renamed_by_name(locations: Locations) -> None:
    """The demo's two identical copies moved together: paired by name.

    Each old copy pairs with the new path of the same rank, the same on every run.
    """
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    photos = locations.data_dir / PHOTOS
    (photos / "Best").mkdir()
    for name in ("IMG_0001.jpg", "IMG_0001 (1).jpg"):
        (photos / "2019/Vacances" / name).rename(photos / "Best" / name)
    plan = prepare_push(runtime, TARGET, anyway=False).plan
    moves = [
        (move.old.path.rsplit("/", 1)[1], move.new.split("/", 2)[2])
        for move in plan.moves
    ]
    assert moves == [
        ("IMG_0001 (1).jpg", "Best/IMG_0001 (1).jpg"),
        ("IMG_0001.jpg", "Best/IMG_0001.jpg"),
    ]
    assert not plan.copies


def test_an_edited_file_is_set_aside_then_copied(locations: Locations) -> None:
    """The previous copy in `.removed/<run>`, the new one in its place."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    photo = locations.data_dir / PHOTOS / "2019/Vacances/IMG_0002.jpg"
    old = photo.read_bytes()
    photo.write_bytes(old + b"edited")
    _lines, proof = backed_up(runtime)
    relative = "C/Family Photos/2019/Vacances/IMG_0002.jpg"
    backup = locations.data_dir / "e/Backup"
    assert (backup / relative).read_bytes() == old + b"edited"
    aside = backup / REMOVED_FOLDER / proof.run_id / relative
    assert aside.read_bytes() == old
    assert proof.renamed == 1


def test_only_purged_or_confirmed_files_leave_the_backup(locations: Locations) -> None:
    """A purged duplicate is set aside; a file deleted by mistake stays."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    photos = locations.data_dir / PHOTOS
    purged = photos / "2019/Vacances/IMG_0001 (1).jpg"
    journal_clean(runtime, purged, ActionKind.QUARANTINE_DUPLICATE)
    purged.unlink()
    (photos / "2019/Vacances/IMG_0003.jpg").unlink()  # by mistake, in the Explorer
    prepared = prepare_push(runtime, TARGET, anyway=False)
    reasons = {
        gone.entry.path.rsplit("/", 1)[1]: gone.reason for gone in prepared.plan.gone
    }
    assert reasons == {
        "IMG_0001 (1).jpg": GoneReason.PURGED,
        "IMG_0003.jpg": GoneReason.UNKNOWN,
    }
    _lines, proof = backed_up(runtime)
    backup = locations.data_dir / "e/Backup/C/Family Photos/2019/Vacances"
    assert not (backup / "IMG_0001 (1).jpg").exists()
    assert (backup / "IMG_0003.jpg").is_file()
    removed = locations.data_dir / "e/Backup" / REMOVED_FOLDER / proof.run_id
    assert (removed / "C/Family Photos/2019/Vacances/IMG_0001 (1).jpg").is_file()


def test_undo_puts_back_what_a_run_set_aside(locations: Locations) -> None:  # pylint: disable=too-many-locals
    """`mh push --undo`: the file back in place, journaled; the copies stay."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    purged = locations.data_dir / PHOTOS / "2019/Vacances/IMG_0001 (1).jpg"
    journal_clean(runtime, purged, ActionKind.QUARANTINE_DUPLICATE)
    purged.unlink()
    _lines, proof = backed_up(runtime)
    target = push_target(runtime, TARGET)
    undo = plan_undo(runtime.locations.journal_dir, proof.run_id, target)
    assert len(undo.lines) == 1
    for line in undo.lines:
        _move, old, new, _size, _mtime = line.split("\t")
        source = target.point / (target.relative(old) or "")
        source.rename(target.point / (target.relative(new) or ""))
    assert record_undone(runtime.locations.journal_dir, proof.run_id, target) == 1
    assert (target.point / "C/Family Photos/2019/Vacances/IMG_0001 (1).jpg").is_file()
    again = plan_undo(runtime.locations.journal_dir, proof.run_id, target)
    assert not again.lines
    restored = summarize(runtime.locations.journal_dir, proof.run_id).restored
    assert restored == 1


def test_undo_of_a_backup_run_is_refused_by_the_container(locations: Locations) -> None:
    """Windows writes the backup: `undo` says to type `mh push --undo`."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    _lines, proof = backed_up(runtime)
    with pytest.raises(JournalError) as refused:
        ensure_undo_ready(runtime, [proof.run_id])
    assert f"mh push --undo {proof.run_id}" in (refused.value.tip or "")
    entries = read_journal(journal_file(runtime.locations.journal_dir, proof.run_id))
    assert all(entry.phase is Phase.PUSH for entry in entries)


def test_a_folder_of_the_backup_not_mounted_now_is_left_alone(
    locations: Locations,
) -> None:
    """A drive not plugged in: its part of the backup is neither gone nor removed."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    other = locations.data_dir / "e/Backup/F/Photos/a.jpg"
    other.parent.mkdir(parents=True)
    other.write_bytes(b"from a drive not plugged in")
    plan = prepare_push(runtime, TARGET, anyway=False).plan
    assert not plan.gone
    backed_up(runtime)
    assert other.is_file()


def test_a_target_overlapping_a_photo_folder_is_refused(locations: Locations) -> None:
    """Inside the photos, or holding them: refused, both named."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    with pytest.raises(MountError, match="overlaps"):
        prepare_push(runtime, "C:\\Family Photos\\Backup", anyway=False)
    with pytest.raises(MountError, match="overlaps"):
        prepare_push(runtime, "C:\\", anyway=False)


def test_the_safety_stop_holds_the_run(locations: Locations) -> None:
    """Most of the photos edited at once: stopped, `--anyway` goes on."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    for path in (locations.data_dir / PHOTOS).rglob("*.jpg"):
        path.write_bytes(path.read_bytes() + b"!")
    stopped = prepare_push(runtime, TARGET, anyway=False)
    assert stopped.stopped
    assert "stop" in plan_lines(stopped)
    assert not prepare_push(runtime, TARGET, anyway=True).stopped


def test_expired_folders_of_removed_are_listed(locations: Locations) -> None:
    """Older than `[push] keep_removed_days`: erased by Windows."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    removed = locations.data_dir / "e/Backup" / REMOVED_FOLDER
    (removed / "20200101-120000").mkdir(parents=True)
    (removed / "29990101-120000").mkdir()
    (removed / "not a run").mkdir()
    prepared = prepare_push(runtime, TARGET, anyway=False)
    assert prepared.expired == (f"{REMOVED_FOLDER}/20200101-120000",)
    assert "expired\tE:\\Backup\\.removed\\20200101-120000" in plan_lines(prepared)


def test_each_reason_a_file_is_gone(locations: Locations) -> None:
    """Confirmed, still in the quarantine, waiting for `review --gone`: said apart."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    vacation = locations.data_dir / PHOTOS / "2019/Vacances"
    journal_clean(runtime, vacation / "IMG_0001.jpg", ActionKind.MARK_GONE)
    quarantined = vacation / "IMG_0002.jpg"
    entry_dir = runtime.locations.journal_dir
    stat = quarantined.stat()
    with JournalWriter.open(journal_file(entry_dir, "20260102-120000")) as journal:
        journal.record(
            JournalEntry(
                seq=1,
                phase=Phase.CLEAN,
                status=Status.DONE,
                action=ActionKind.QUARANTINE_CHOSEN,
                path=str(quarantined),
                host_path=runtime.mapper.to_host(quarantined),
                size=stat.st_size,
                mtime_ns=stat.st_mtime_ns,
            )
        )
    (runtime.locations.quarantine_dir / "20260102-120000" / "x").mkdir(parents=True)
    (runtime.locations.quarantine_dir / "20260102-120000" / "x" / "a").write_bytes(b"")
    pending = vacation / "IMG_0003.jpg"
    index = runtime.index_file
    assert index is not None
    with FactsRepository.open(index) as repository:
        repository.connection.execute(
            "INSERT INTO gone_files (path, size, mtime_ns, partial_digest, gone_at)"
            " VALUES (?, 1, 1, 'x', '2026-01-01T00:00:00+00:00')",
            (str(pending),),
        )
        repository.connection.commit()
    for name in ("IMG_0001.jpg", "IMG_0002.jpg", "IMG_0003.jpg"):
        (vacation / name).unlink()
    plan = prepare_push(runtime, TARGET, anyway=False).plan
    reasons = {g.entry.path.rsplit("/", 1)[1]: g.reason for g in plan.gone}
    assert reasons == {
        "IMG_0001.jpg": GoneReason.CONFIRMED,
        "IMG_0002.jpg": GoneReason.QUARANTINE,
        "IMG_0003.jpg": GoneReason.PENDING,
    }
    assert [g.entry.path.rsplit("/", 1)[1] for g in plan.removals] == ["IMG_0001.jpg"]


def test_a_broken_photo_never_replaces_its_backup(locations: Locations) -> None:
    """The audit found it broken, unchanged since: robocopy is told to skip it."""
    build_demo(locations.data_dir)
    runtime = mounted(locations)
    backed_up(runtime)
    photo = locations.data_dir / PHOTOS / "2019/Vacances/IMG_0002.jpg"
    good = photo.read_bytes()
    photo.write_bytes(good[:100])
    stat = photo.stat()
    index = runtime.index_file
    assert index is not None
    with FactsRepository.open(index) as repository:
        repository.connection.execute(
            "INSERT OR REPLACE INTO files (path, size, mtime_ns, broken_reason)"
            " VALUES (?, ?, ?, 'truncated')",
            (str(photo), stat.st_size, stat.st_mtime_ns),
        )
        repository.connection.commit()
    lines, proof = backed_up(runtime)
    copy = locations.data_dir / "e/Backup/C/Family Photos/2019/Vacances/IMG_0002.jpg"
    assert copy.read_bytes() == good
    assert any(line.startswith("broken\t") for line in lines)
    assert not proof.missing  # a broken one is not missing
