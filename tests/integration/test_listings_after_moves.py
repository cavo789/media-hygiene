"""The folders the tool itself changes are read again by the next walk.

On a Windows drive shared with Docker Desktop, a folder's modification time seen in
the container may not change when files leave or come back: the walk would then trust
the listing the index kept and list files that are gone (a `review` after
`clean --decisions` showing the shots set aside). Each test freezes every folder's
time back to what the index saw (`os.utime`), then walks again.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanMode, CleanService
from media_hygiene.services.listing import list_media
from media_hygiene.services.undo import undo_run
from tests.support.cli import run
from tests.support.media import MediaFactory
from tests.support.runtime import make_runtime
from tests.support.sorting import PARTY, build_library, name_first_event

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_PHOTOS = "c/Photos"
_KEEP: Layer = {"folders": {"preferred": ["C:\\Photos\\Keep"]}}


def _tree(data: Path) -> None:
    """Kept photos, a folder of copies only (emptied by a clean), a mixed folder."""
    media = MediaFactory(data)
    first = media.image(f"{_PHOTOS}/Keep/one.jpg", seed=11)
    second = media.image(f"{_PHOTOS}/Keep/two.jpg", seed=12)
    media.copy(first, f"{_PHOTOS}/Old/Trip/one.jpg")
    media.copy(second, f"{_PHOTOS}/Old/Trip/two.jpg")
    media.copy(first, f"{_PHOTOS}/Mixed/one.jpg")
    media.image(f"{_PHOTOS}/Mixed/other.jpg", seed=13)


def _runtime(locations: Locations) -> Runtime:
    """A runtime where `c/Photos` is the mounted folder."""
    mounts = MountTable(frozenset({locations.data_dir / _PHOTOS}))
    return replace(make_runtime(locations, _KEEP), mounts=mounts)


def _times(data: Path) -> dict[Path, int]:
    """Every folder's modification time, as the index just saw it."""
    folders = [data, *(path for path in data.rglob("*") if path.is_dir())]
    return {folder: folder.stat().st_mtime_ns for folder in folders}


def _freeze(times: dict[Path, int]) -> None:
    """Put the times of the folders still there back, as Docker Desktop may."""
    for folder, mtime_ns in times.items():
        if folder.is_dir():
            os.utime(folder, ns=(mtime_ns, mtime_ns))


def _listed(runtime: Runtime) -> frozenset[Path]:
    """The media files the next walk lists; it must read every folder it visits."""
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    found = list_media(runtime, roots, NullProgress())
    assert not found.unreadable
    return frozenset(file.path for file in found.files)


def _clean(runtime: Runtime, *, delete: bool = False) -> tuple[str, dict[Path, int]]:
    """Audit (the listings saved), then clean; the folder times before the clean."""
    findings = AuditService(runtime, NullProgress()).run()
    times = _times(runtime.locations.data_dir)
    service = CleanService(runtime, NullProgress())
    service.ensure_ready(CleanMode(delete=delete))
    plan = service.feasible(replace(findings.plan, delete_copies=delete))
    run_id, _outcome = service.execute(plan)
    return run_id, times


def test_a_file_moved_to_the_quarantine_is_no_longer_listed(
    locations: Locations,
) -> None:
    """Mixed/one.jpg set aside: the walk reads Mixed again, its time frozen."""
    data = locations.data_dir
    _tree(data)
    runtime = _runtime(locations)
    _run_id, times = _clean(runtime)
    moved = data / _PHOTOS / "Mixed" / "one.jpg"
    assert not moved.exists()
    _freeze(times)
    listed = _listed(runtime)
    assert moved not in listed
    assert data / _PHOTOS / "Mixed" / "other.jpg" in listed


def test_a_file_deleted_is_no_longer_listed(locations: Locations) -> None:
    """`clean --delete`: the copy deleted is not listed, its folder's time frozen."""
    data = locations.data_dir
    _tree(data)
    runtime = _runtime(locations)
    _run_id, times = _clean(runtime, delete=True)
    deleted = data / _PHOTOS / "Mixed" / "one.jpg"
    assert not deleted.exists()
    _freeze(times)
    assert deleted not in _listed(runtime)


def test_a_folder_removed_is_neither_listed_nor_unreadable(
    locations: Locations,
) -> None:
    """Old/Trip emptied and removed (0202): its parent is read again, not trusted."""
    data = locations.data_dir
    _tree(data)
    runtime = _runtime(locations)
    _run_id, times = _clean(runtime)
    assert not (data / _PHOTOS / "Old").exists()
    _freeze(times)
    listed = _listed(runtime)  # no folder reported unreadable
    assert not any(data / _PHOTOS / "Old" in path.parents for path in listed)


def test_undo_lists_the_files_and_folders_put_back(locations: Locations) -> None:
    """After undo, the restored files and recreated folders are listed again."""
    data = locations.data_dir
    _tree(data)
    runtime = _runtime(locations)
    run_id, _before = _clean(runtime)
    _listed(runtime)  # the listings of the cleaned tree saved
    times = _times(data)
    undo_run(runtime, run_id, NullProgress())
    _freeze(times)
    listed = _listed(runtime)
    assert data / _PHOTOS / "Mixed" / "one.jpg" in listed
    assert data / _PHOTOS / "Old" / "Trip" / "one.jpg" in listed


def test_sort_and_its_undo_are_followed_by_the_walk(
    cli: CliRunner, locations: Locations
) -> None:
    """The files `sort` moved are listed where they went, then back after undo."""
    data = locations.data_dir
    shutil.rmtree(data)
    build_library(data)
    assert run(cli, "classify").exit_code == 0
    (workbook,) = locations.reports_dir.glob("*-classify/classify.xlsx")
    name_first_event(workbook)
    runtime = make_runtime(locations)
    party = data / PARTY / "IMG_0000.jpg"
    assert party in _listed(runtime)
    times = _times(data)
    result = run(cli, "sort", "--yes")
    assert result.exit_code == 0, result.output
    assert not party.exists()
    _freeze(times)
    listed = _listed(runtime)
    assert party not in listed
    assert any(path.name == party.name for path in listed)
    times = _times(data)
    assert run(cli, "undo").exit_code == 0
    _freeze(times)
    assert party in _listed(runtime)
