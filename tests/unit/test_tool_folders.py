"""Tool folders never mixed with the photos; their deletions stay in their own files."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path

import pytest
from pydantic import ValidationError

from media_hygiene.actions.purge import purge_run, quarantine_runs
from media_hygiene.config.sort_settings import SortSettings
from media_hygiene.constants import SUMMARY_FILE_NAME, RunKind
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.paths.mounts import MountTable
from media_hygiene.paths.tool_overlaps import DataScope, tool_overlaps
from media_hygiene.report.index_page import prune_reports
from media_hygiene.report.summary import ReportSummary

PHOTOS = Path("/data/c/Photos")
QUARANTINE = Path("/quarantine")
NATIVE = (
    "36 35 0:30 / / rw - overlay overlay rw\n"
    "40 36 8:1 /home/me/Photos /data/c/Photos rw - ext4 /dev/sda1 rw\n"
    "41 36 8:1 /home/me/Photos/q /quarantine rw - ext4 /dev/sda1 rw\n"
    "42 36 8:1 /home/me/journal /journal rw - ext4 /dev/sda1 rw\n"
    "43 36 8:1 /home/me /reports rw - ext4 /dev/sda1 rw\n"
)
DESKTOP = (
    "50 36 0:60 /run/desktop/mnt/host/c/Photos /data/c/Photos rw - fakeowner x rw\n"
    "51 36 0:61 /run/desktop/mnt/host/c/photos/Quarantine /quarantine rw - x y rw\n"
)


def overlaps(table: str, tmp_path: Path, *excluded: Path) -> set[MountKind]:
    """The tool folders the mount table mixes with `/data/c/Photos`."""
    info = tmp_path / "mountinfo"
    info.write_text(table)
    scope = DataScope(MountTable.current(info), (PHOTOS,), excluded)
    tools = [
        (kind, Path(f"/{kind.value}"))
        for kind in (MountKind.QUARANTINE, MountKind.JOURNAL, MountKind.REPORTS)
    ]
    return {overlap.kind for overlap in tool_overlaps(scope, tools)}


def test_host_folders_inside_or_around_the_photos_are_found(tmp_path: Path) -> None:
    """Same device: the quarantine inside the photos, the photos inside the reports."""
    assert overlaps(NATIVE, tmp_path) == {MountKind.QUARANTINE, MountKind.REPORTS}


def test_windows_folders_are_compared_ignoring_case(tmp_path: Path) -> None:
    r"""`C:\photos\Quarantine` lies in `C:\Photos`, whatever the case."""
    assert overlaps(DESKTOP, tmp_path) == {MountKind.QUARANTINE}


def test_a_tool_folder_in_an_excluded_folder_is_allowed(tmp_path: Path) -> None:
    """Never read: the excluded folder keeps it out of every walk."""
    assert overlaps(NATIVE, tmp_path, PHOTOS / "q") == {MountKind.REPORTS}


def test_container_paths_alone_tell_an_overlap() -> None:
    """`MEDIA_HYGIENE_QUARANTINE_DIR` under a data folder, or a data folder below."""
    scope = DataScope(MountTable(frozenset()), (PHOTOS,))
    inside = (MountKind.QUARANTINE, PHOTOS / "q")
    around = (MountKind.CACHE, Path("/data"))
    apart = (MountKind.JOURNAL, Path("/journal"))
    found = tool_overlaps(scope, [inside, around, apart])
    assert [item.kind for item in found] == [MountKind.QUARANTINE, MountKind.CACHE]


@pytest.mark.parametrize(
    "name", ["IMG_1.JPG", "clip.mov", "raw.CR2", "edit.xmp", "*.db", "a/Thumbs.db", " "]
)
def test_a_junk_name_is_never_a_photo_nor_a_pattern(name: str) -> None:
    """`sort` would set it aside as junk: refused when the settings load."""
    with pytest.raises(ValidationError, match="junk_files"):
        SortSettings(junk_files=("Thumbs.db", name))
    assert "thumbs.db" in SortSettings(junk_files=("Thumbs.db",)).junk_names


def test_purge_deletes_run_folders_only(tmp_path: Path) -> None:
    """A folder not named like a run, or a link to one, is never listed nor deleted."""
    run = tmp_path / "20260925-183015-2"
    (run / "c").mkdir(parents=True)
    (run / "c" / "IMG_1.jpg").write_bytes(b"set aside")
    photos = tmp_path / "Photos"
    photos.mkdir()
    (photos / "IMG_2.jpg").write_bytes(b"a photo")
    (tmp_path / "20260101-000000").symlink_to(photos)
    assert quarantine_runs(tmp_path) == ["20260925-183015-2"]
    for name in ("Photos", "20260101-000000"):
        with pytest.raises(OSError, match="not the quarantine of a run"):
            purge_run(tmp_path, name)
    assert purge_run(tmp_path, run.name) == len(b"set aside")
    assert (photos / "IMG_2.jpg").exists()


def report(folder: Path, created: str, name: str) -> None:
    """Write a report folder with its summary; `name` is what the summary claims."""
    folder.mkdir(parents=True)
    summary = ReportSummary(
        folder=name,
        kind=RunKind.AUDIT,
        created_at=datetime.fromisoformat(created),
        files_scanned=1,
        duplicate_groups=0,
        duplicate_files=0,
        reclaimable_bytes=0,
        broken_files=0,
    )
    (folder / SUMMARY_FILE_NAME).write_text(summary.model_dump_json())


def test_prune_deletes_report_folders_only(tmp_path: Path) -> None:
    """A folder the tool did not name, or a summary naming another folder: kept."""
    reports = tmp_path / "reports"
    report(reports / "20260101-000000-audit", "2026-01-01T00:00:00Z", "x")
    report(reports / "Holidays", "2026-01-02T00:00:00Z", "Holidays")
    report(reports / "20260103-000000-audit", "2026-01-03T00:00:00Z", "..")
    report(reports / "20260104-000000-audit", "2026-01-04T00:00:00Z", "y")
    removed = prune_reports(reports, 1)
    assert removed == ["20260103-000000-audit", "20260101-000000-audit"]
    assert sorted(path.name for path in reports.iterdir() if path.is_dir()) == [
        "20260104-000000-audit",
        "Holidays",
    ]
    assert tmp_path.is_dir()
