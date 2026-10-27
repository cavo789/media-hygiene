"""`import` (0245): what only a backup holds is copied, proven, journaled, undoable.

The backup (a NAS share mounted as a backup folder) is never touched; a second run
copies nothing; `undo` removes the copies; a near copy and identical twins are kept
apart; a copy edited since is kept by `undo`.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from typing import TYPE_CHECKING, Final

from typer.testing import CliRunner

from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.import_run import ImportService
from media_hygiene.services.import_source import from_folder
from media_hygiene.services.undo import undo_run
from tests.support.cli import point_mounts, run
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    import pytest

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_BACKUP: Final[Layer] = {"folders": {"backups": ["D:\\backup"]}}
FROM_D: Final = from_folder("D")  # a backup on drive D: (0378)


def library_and_nas(locations: Locations) -> tuple[Path, Path]:
    """Photos on drive C, a NAS share as the backup on drive D; the folders."""
    photos = locations.data_dir / "c" / "Photos"
    nas = locations.data_dir / "d" / "backup"
    (photos / "2024").mkdir(parents=True)
    (nas / "2024").mkdir(parents=True)
    scene(1).save(photos / "2024" / "IMG_0001.jpg", quality=90)
    shutil.copy2(photos / "2024" / "IMG_0001.jpg", nas / "2024" / "IMG_0001.jpg")
    (nas / "2019" / "Été").mkdir(parents=True)
    scene(7).save(nas / "2019" / "Été" / "IMG_0007.jpg", quality=90)
    return photos, nas


def mounted(locations: Locations) -> Runtime:
    """The photo folder and the NAS mounted apart, as `mh` mounts them."""
    runtime = make_runtime(locations, _BACKUP)
    folders = frozenset(
        {locations.data_dir / "c" / "Photos", locations.data_dir / "d" / "backup"}
    )
    return replace(runtime, mounts=MountTable(folders, (), ()))


def import_once(runtime: Runtime) -> tuple[ImportService, str, tuple[Path, ...]]:
    """Plan, then copy; the run and the copies."""
    service = ImportService(runtime, NullProgress())
    service.ensure_ready()
    plan = service.prepare()
    result = service.execute(plan, lambda: False)
    return service, result.run_id, result.copied


def test_only_the_nas_photo_is_copied_and_proven(locations: Locations) -> None:
    """Copied below `From D`, the backup's folders kept, same bytes and time."""
    photos, nas = library_and_nas(locations)
    before = {path: path.read_bytes() for path in nas.rglob("*") if path.is_file()}
    runtime = mounted(locations)
    _service, _run, copied = import_once(runtime)
    source = nas / "2019" / "Été" / "IMG_0007.jpg"
    target = photos / FROM_D / "2019" / "Été" / "IMG_0007.jpg"
    assert copied == (target,)
    assert target.read_bytes() == source.read_bytes()
    assert target.stat().st_mtime_ns == source.stat().st_mtime_ns
    assert {p: p.read_bytes() for p in nas.rglob("*") if p.is_file()} == before


def test_a_second_import_copies_nothing(locations: Locations) -> None:
    """The copies are in the library now: nothing left only on the NAS."""
    library_and_nas(locations)
    runtime = mounted(locations)
    import_once(runtime)
    service = ImportService(runtime, NullProgress())
    assert not service.prepare().jobs


def test_undo_removes_the_copies_and_their_folders(locations: Locations) -> None:
    """`undo` removes each copy, then the folders the run created, empty."""
    photos, nas = library_and_nas(locations)
    runtime = mounted(locations)
    _service, run_id, copied = import_once(runtime)
    outcome = undo_run(runtime, run_id, NullProgress())
    assert outcome.done >= 1
    assert not any(path.exists() for path in copied)
    assert not (photos / FROM_D).exists()
    assert (nas / "2019" / "Été" / "IMG_0007.jpg").is_file()


def test_undo_keeps_a_copy_edited_since(locations: Locations) -> None:
    """A copy changed after the import is the user's now: kept, the reason told."""
    library_and_nas(locations)
    runtime = mounted(locations)
    _service, run_id, (copy,) = import_once(runtime)
    copy.write_bytes(copy.read_bytes() + b"edited")
    outcome = undo_run(runtime, run_id, NullProgress())
    assert copy.is_file()
    assert any("changed since" in item.reason for item in outcome.skipped)


def test_twins_on_the_nas_are_copied_once(locations: Locations) -> None:
    """Two identical files only on the NAS: one copy, the other counted."""
    _photos, nas = library_and_nas(locations)
    twin = nas / "2020" / "copy of IMG_0007.jpg"
    twin.parent.mkdir()
    shutil.copy2(nas / "2019" / "Été" / "IMG_0007.jpg", twin)
    runtime = mounted(locations)
    plan = ImportService(runtime, NullProgress()).prepare()
    assert len(plan.jobs) == 1
    assert plan.twins == 1


def test_a_near_copy_in_the_library_is_listed_apart(locations: Locations) -> None:
    """The NAS keeps the large photo, the library a smaller one: not proposed."""
    photos, nas = library_and_nas(locations)
    large = scene(5)
    large.save(nas / "2024" / "IMG_0005.jpg", quality=95)
    small = large.resize((large.width // 2, large.height // 2))
    small.save(photos / "2024" / "IMG_0005-small.jpg", quality=80)
    runtime = mounted(locations)
    plan = ImportService(runtime, NullProgress()).prepare()
    assert [file.path.name for file in plan.near] == ["IMG_0005.jpg"]
    assert all(job.source.name != "IMG_0005.jpg" for job in plan.jobs)


def test_an_earlier_from_nas_folder_is_not_imported_again(
    locations: Locations,
) -> None:
    """0378: copies made under `From NAS` before the rename are held: nothing new."""
    photos, nas = library_and_nas(locations)
    earlier = photos / "From NAS" / "2019" / "Été" / "IMG_0007.jpg"
    earlier.parent.mkdir(parents=True)
    shutil.copy2(nas / "2019" / "Été" / "IMG_0007.jpg", earlier)
    plan = ImportService(mounted(locations), NullProgress()).prepare()
    assert not plan.jobs
    assert not (photos / FROM_D).exists()


def test_a_folder_never_declared_is_imported_and_only_read(
    locations: Locations,
) -> None:
    r"""0378: `mh import E:\DCIM`, no backup in the settings: `From E`, E: unchanged."""
    photos, _nas = library_and_nas(locations)
    card = locations.data_dir / "e" / "DCIM"
    (card / "100CANON").mkdir(parents=True)
    scene(8).save(card / "100CANON" / "IMG_0008.jpg", quality=90)
    before = {p: p.read_bytes() for p in card.rglob("*") if p.is_file()}
    runtime = make_runtime(locations, {"folders": {"backups": ["E:\\DCIM"]}})
    folders = frozenset({photos, card})
    runtime = replace(runtime, mounts=MountTable(folders, (), ()))
    _service, _run, copied = import_once(runtime)
    assert copied == (photos / from_folder("E") / "100CANON" / "IMG_0008.jpg",)
    assert {p: p.read_bytes() for p in card.rglob("*") if p.is_file()} == before


def test_the_command_takes_a_folder_instead_of_the_backups(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    r"""0378: `import E:\DCIM --yes`, no backup declared: that folder is read."""
    point_mounts(locations, monkeypatch)
    card = locations.data_dir / "e" / "DCIM"
    card.mkdir(parents=True)
    scene(8).save(card / "IMG_0008.jpg", quality=90)
    result = run(CliRunner(), "import", "E:\\DCIM", "--yes")
    assert result.exit_code == 0, result.output
    assert (locations.data_dir / from_folder("E") / "IMG_0008.jpg").is_file()
    assert (card / "IMG_0008.jpg").is_file()


def test_the_phone_reaching_the_container_is_refused(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0379: `import --phone` is the mh.ps1's; in the container one line, status 2."""
    point_mounts(locations, monkeypatch)
    result = run(CliRunner(), "import", "--phone")
    assert result.exit_code == 2, result.output
    assert "mh import --phone is for Windows only" in result.output
    assert not (locations.data_dir / from_folder("E")).exists()
