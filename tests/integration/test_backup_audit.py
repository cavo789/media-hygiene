"""A backup folder: compared, never changed — what is missing on either side (0204)."""

from __future__ import annotations

import csv
import json
import sqlite3
from contextlib import closing
from pathlib import Path
from typing import TYPE_CHECKING

import numpy as np
from PIL import Image

from media_hygiene.console.backup_view import show_backups
from media_hygiene.constants import SUMMARY_FILE_NAME, RunKind, Sizes
from media_hygiene.report.backup_views import (
    MISSING_CSV_FILE_NAME,
    ONLY_CSV_FILE_NAME,
)
from media_hygiene.report.csv_export import CSV_ENCODING
from media_hygiene.report.views import ReportRecord
from media_hygiene.scan import exact, hashing
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.clean import CleanService
from media_hygiene.services.crosscheck import czkawka_command
from media_hygiene.services.reporting import write_report
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    import pytest

    from media_hygiene.config.layers import Layer
    from media_hygiene.paths.locations import Locations
    from media_hygiene.plan.models import AuditFindings
    from media_hygiene.services.runtime import Runtime
    from tests.support.media import MediaFactory

_BACKUP: Layer = {"folders": {"backups": ["D:\\backup"]}}


def library_and_backup(media: MediaFactory) -> dict[str, Path]:
    """Photos in C:, a backup in D:, each case of the TODO once.

    Returns:
        The files, by role.
    """
    both = media.image("c/Photos/both.jpg", seed=1)
    resized = media.image("c/Photos/resized.jpg", seed=4)
    twin = media.image("c/Photos/2019/twin.jpg", seed=5)
    files = {
        "both": both,
        "library only": media.image("c/Photos/library.jpg", seed=2),
        "resized": resized,
        "twin": twin,
        "twin copy": media.copy(twin, "c/Photos/Copies/twin.jpg"),
        "backed": media.copy(both, "d/backup/both.jpg"),
        "backup only": media.image("d/backup/old disk/old.jpg", seed=3),
        "backup twin": media.copy(twin, "d/backup/twin.jpg"),
        "backup resized": media.root / "d/backup/resized.jpg",
    }
    with Image.open(resized) as picture:
        smaller = picture.resize((picture.width // 2, picture.height // 2))
        smaller.save(files["backup resized"])
    return files


def audit(runtime: Runtime) -> AuditFindings:
    """Audit the data mount."""
    return AuditService(runtime, NullProgress()).run()


def test_each_side_says_what_the_other_lacks(
    locations: Locations, media: MediaFactory
) -> None:
    """Missing: the library's file alone and the resized one; only: the backup's."""
    files = library_and_backup(media)
    findings = audit(make_runtime(locations, _BACKUP))
    (backup,) = findings.backups
    assert backup.folder == locations.data_dir / "d" / "backup"
    assert backup.files == 4
    assert {f.path for f in backup.missing} == {
        files["library only"],
        files["resized"],
    }
    assert {f.path for f in backup.only} == {
        files["backup only"],
        files["backup resized"],
    }
    assert backup.only_size == sum(f.size for f in backup.only)


def test_a_backup_copy_is_never_the_reason_a_file_goes(
    locations: Locations, media: MediaFactory
) -> None:
    """Only the library's own twin is planned; the backup is left out of every list."""
    files = library_and_backup(media)
    findings = audit(make_runtime(locations, _BACKUP))
    backup_dir = locations.data_dir / "d" / "backup"
    (decision,) = findings.plan.decisions
    assert {decision.keeper.path, *(f.path for f in decision.removable)} == {
        files["twin"],
        files["twin copy"],
    }
    assert all(len(group.files) == 2 for group in findings.groups)
    planned = findings.plan.removed | {f.path for f in findings.plan.orphans}
    assert not any(path.is_relative_to(backup_dir) for path in planned)
    seen = {
        f.path
        for near in findings.similar.near
        for f in (near.keeper, *near.removable, *near.protected)
    }
    assert not any(path.is_relative_to(backup_dir) for path in seen)


def test_clean_never_touches_the_backup(
    locations: Locations, media: MediaFactory
) -> None:
    """After `clean`, every backup file is there, byte for byte; `both` stays too."""
    files = library_and_backup(media)
    contents = {name: path.read_bytes() for name, path in files.items()}
    runtime = make_runtime(locations, _BACKUP)
    service = CleanService(runtime, NullProgress())
    _run_id, outcome = service.execute(service.feasible(audit(runtime).plan))
    assert outcome.done == 1
    for name in ("backed", "backup only", "backup twin", "backup resized", "both"):
        assert files[name].read_bytes() == contents[name]


def test_without_backup_the_old_audit_is_unchanged(
    locations: Locations, media: MediaFactory
) -> None:
    """No backup folder: the backup's copies are ordinary copies, as before."""
    library_and_backup(media)
    findings = audit(make_runtime(locations))
    assert not findings.backups
    assert len(findings.plan.decisions) == 2


def test_console_report_and_csv_files_say_both(
    locations: Locations, media: MediaFactory
) -> None:
    """Two lines in the console, a section in the report, two CSV files."""
    files = library_and_backup(media)
    runtime = make_runtime(locations, _BACKUP)
    findings = audit(runtime)
    show_backups(runtime, findings.backups)
    said = output_of(runtime)
    assert "2 files of your photos are not in this backup" in said
    assert "2 files are only in it" in said
    report = write_report(runtime, ReportRecord(RunKind.AUDIT, findings))
    assert report is not None
    page = report.read_text(encoding="utf-8")
    assert 'id="backups"' in page
    assert str(runtime.mapper.to_host(files["backup only"])) in page
    with (report.parent / MISSING_CSV_FILE_NAME).open(encoding=CSV_ENCODING) as f:
        missing = list(csv.reader(f))
    with (report.parent / ONLY_CSV_FILE_NAME).open(encoding=CSV_ENCODING) as f:
        only = list(csv.reader(f))
    assert len(missing) == len(only) == 3  # the header, then two files each
    # What `mh menu` proposes to import: the files only it holds, never dealt with.
    summary = json.loads((report.parent / SUMMARY_FILE_NAME).read_text("utf-8"))
    assert summary["backup_only"] == sum(len(b.to_import) for b in findings.backups)
    assert summary["backup_only"] > 0
    assert {row[1] for row in missing[1:]} == {
        runtime.mapper.to_host(files["library only"]),
        runtime.mapper.to_host(files["resized"]),
    }


def test_czkawka_leaves_the_backup_out(locations: Locations) -> None:
    """The command printed for Czkawka excludes the backup folder too."""
    (locations.data_dir / "d" / "backup").mkdir(parents=True)
    command = czkawka_command(make_runtime(locations, _BACKUP))
    assert locations.data_dir / "d" / "backup" in command.scope.excluded


def test_no_backup_file_is_read_whole(
    locations: Locations, media: MediaFactory, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The audit hashes the library's twins in full, never a backup file (0274)."""
    files = library_and_backup(media)
    backup_dir = locations.data_dir / "d" / "backup"
    read: list[Path] = []
    whole = hashing.full_digest

    def spy(path: Path) -> str:
        read.append(path)
        return whole(path)

    monkeypatch.setattr(exact, "full_digest", spy)
    runtime = make_runtime(locations, _BACKUP)
    findings = audit(runtime)
    assert not any(path.is_relative_to(backup_dir) for path in read)
    assert runtime.index_file is not None
    with closing(sqlite3.connect(runtime.index_file)) as connection:
        rows = connection.execute("SELECT path, partial_digest, full_digest FROM files")
        digests = {Path(path): (partial, full) for path, partial, full in rows}
    assert digests[files["twin"]][1]  # the library's twins: proven in full
    assert digests[files["backed"]][0]  # the backup's copies: 128 KiB read
    assert not any(
        full
        for path, (_partial, full) in digests.items()
        if path.is_relative_to(backup_dir)
    )
    (backup,) = findings.backups
    assert {f.path for f in backup.only} == {
        files["backup only"],
        files["backup resized"],
    }


def test_a_backup_file_differing_only_in_its_middle_counts_as_a_copy(
    locations: Locations, media: MediaFactory
) -> None:
    """Same size, same first and last 64 KiB: covered, the documented trade-off."""
    photo = media.root / "c/Photos/noise.jpg"
    photo.parent.mkdir(parents=True)
    pixels = np.random.default_rng(7).integers(0, 256, (512, 512, 3), dtype=np.uint8)
    Image.fromarray(pixels).save(photo, quality=95)
    content = bytearray(photo.read_bytes())
    assert len(content) > 3 * Sizes.PARTIAL_HASH
    content[len(content) // 2] ^= 0xFF
    altered = media.root / "d/backup/noise.jpg"
    altered.parent.mkdir(parents=True)
    altered.write_bytes(content)
    (backup,) = audit(make_runtime(locations, _BACKUP)).backups
    assert backup.files == 1
    assert not backup.missing
    assert not backup.only
