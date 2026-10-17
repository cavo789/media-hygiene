"""The files an audit proves gone and does not follow are recorded (TODO 0224).

One test per event that makes a file absent from a walk: deleted, renamed with its
folder (followed), on a drive not mounted this time, back after a while.
"""

from __future__ import annotations

import shutil
from dataclasses import replace
from typing import TYPE_CHECKING

from media_hygiene.index.gone_rows import gone_count, gone_records
from media_hygiene.index.repository import FactsRepository
from media_hygiene.paths.mounts import MountTable
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from tests.support.runtime import make_runtime
from tests.support.scenes import scene

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.index.gone_rows import GoneRecord
    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings


def photos(folder: Path, *seeds: int) -> list[Path]:
    """Distinct photos in a folder."""
    folder.mkdir(parents=True, exist_ok=True)
    paths = [folder / f"IMG_{seed:04d}.jpg" for seed in seeds]
    for seed, path in zip(seeds, paths, strict=True):
        scene(seed).save(path, quality=90)
    return paths


def audit(locations: Locations, *mounted: Path) -> AuditFindings:
    """Audit the data mount, or only the folders `mounted`."""
    runtime = make_runtime(locations)
    if mounted:
        runtime = replace(runtime, mounts=MountTable(frozenset(mounted), (), ()))
    return AuditService(runtime, NullProgress()).run()


def recorded(locations: Locations) -> tuple[GoneRecord, ...]:
    """The files gone the index records."""
    with FactsRepository.open(locations.index_file) as repository:
        return gone_records(repository.connection)


def test_a_deleted_file_is_recorded(locations: Locations) -> None:
    """Its size, time, partial digest, the moment it was found gone; counted."""
    gone, _kept = photos(locations.data_dir / "c" / "Photos", 1, 2)
    stat = gone.stat()
    audit(locations)
    gone.unlink()
    findings = audit(locations)
    (record,) = recorded(locations)
    assert (record.path, record.size, record.mtime_ns) == (
        str(gone),
        stat.st_size,
        stat.st_mtime_ns,
    )
    assert record.partial_digest
    assert record.gone_at
    assert findings.gone == 1


def test_a_folder_renamed_records_nothing(locations: Locations) -> None:
    """The files are followed to their new path (0147): nothing is gone."""
    folder = locations.data_dir / "c" / "Photos" / "2024"
    photos(folder, 1, 2)
    audit(locations)
    folder.rename(folder.with_name("2024 Summer"))
    assert audit(locations).gone == 0
    assert not recorded(locations)


def test_a_drive_not_mounted_records_nothing(locations: Locations) -> None:
    """A drive not mounted this time proves nothing gone."""
    drive_c, drive_d = locations.data_dir / "c", locations.data_dir / "d"
    photos(drive_c / "Photos", 1)
    photos(drive_d / "Backup", 2)
    audit(locations, drive_c, drive_d)
    assert audit(locations, drive_c).gone == 0
    assert not recorded(locations)


def test_a_file_that_reappears_drops_its_record(locations: Locations) -> None:
    """Moved back from a disk plugged in again: same size, time and digest."""
    gone, _kept = photos(locations.data_dir / "c" / "Photos", 1, 2)
    keep = gone.with_name("kept-away.bin")
    audit(locations)
    shutil.move(gone, keep)  # out of the walk: not a media extension
    audit(locations)
    assert len(recorded(locations)) == 1
    back = gone.parent / "Restored" / gone.name
    back.parent.mkdir()
    shutil.copy2(keep, back)  # keeps the modification time
    assert audit(locations).gone == 0
    with FactsRepository.open(locations.index_file) as repository:
        assert gone_count(repository.connection) == 0


def test_a_copy_still_there_drops_the_record(locations: Locations) -> None:
    """Deleting one of two copies loses nothing of the content: nothing to remember."""
    gone, _kept = photos(locations.data_dir / "c" / "Photos", 1, 2)
    twin = gone.parent / "Other" / "twin.jpg"
    twin.parent.mkdir()
    twin.write_bytes(gone.read_bytes())  # another modification time
    audit(locations)
    gone.unlink()
    assert audit(locations).gone == 0
    assert not recorded(locations)
