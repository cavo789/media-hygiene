"""Intruder files (0410): counted by the walk, reported, set aside only when picked."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.report.decisions import read_decisions
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.intruder_pick import (
    FOUND_BY,
    IntruderPick,
    current_intruders,
    set_intruders_aside,
)
from media_hygiene.services.listing import list_media
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from tests.support.media import MediaFactory

_ZIP = b"PK" + b"z" * 98
_PDF = b"%PDF" + b"p" * 46


def _tree(media: MediaFactory, locations: Locations) -> Path:
    """Photos with a zip, a pdf below, companions, and a zip in a protected folder."""
    media.image("c/Photos/a.jpg")
    photos = locations.data_dir / "c" / "Photos"
    (photos / "a.jpg.xmp").write_text("<x/>")
    (photos / "Thumbs.db").write_bytes(b"t")
    (photos / "desktop.ini").write_text("[x]")
    (photos / "orphan.json").write_text("{}")
    (photos / "b.zip").write_bytes(_ZIP)
    (photos / "Trip").mkdir()
    (photos / "Trip" / "c.pdf").write_bytes(_PDF)
    media.image("c/Kept/k.jpg", seed=3)
    (locations.data_dir / "c" / "Kept" / "x.zip").write_bytes(_ZIP)
    return photos


def test_a_walk_from_the_index_finds_the_same_intruders(
    media: MediaFactory, locations: Locations
) -> None:
    """Fresh listing, then the listings the index kept: the same files, same sizes."""
    _tree(media, locations)
    runtime = make_runtime(locations)
    roots = runtime.mounts.data_roots(locations.data_dir)
    fresh = list_media(runtime, roots, NullProgress())
    again = list_media(runtime, roots, NullProgress())
    assert again.reused > 0
    assert sorted(fresh.intruders, key=str) == sorted(again.intruders, key=str)
    names = sorted(item.path.name for item in fresh.intruders)
    assert names == ["b.zip", "c.pdf", "x.zip"]


def test_the_audit_says_it_and_the_report_lists_them(
    cli: CliRunner, media: MediaFactory, locations: Locations
) -> None:
    """One line at the audit's end; a section and intruders.csv in the report."""
    _tree(media, locations)
    result = run(cli, "audit")
    assert result.exit_code == 0, result.output
    said = " ".join(result.output.split())
    assert "🧹 3 files that are not photos or videos (zip, pdf)" in said
    (folder,) = (p.parent for p in locations.reports_dir.glob("*-audit/report.html"))
    assert "Intruder files" in (folder / "report.html").read_text(encoding="utf-8")
    rows = (folder / "intruders.csv").read_text(encoding="utf-8-sig").splitlines()
    assert len(rows) == 4
    assert any("b.zip" in row for row in rows)


def test_nothing_is_said_without_intruders(
    cli: CliRunner, media: MediaFactory, locations: Locations
) -> None:
    """Companions only: no line, no CSV."""
    media.image("c/Photos/a.jpg")
    (locations.data_dir / "c" / "Photos" / "Thumbs.db").write_bytes(b"t")
    result = run(cli, "audit")
    assert result.exit_code == 0, result.output
    assert "🧹" not in result.output
    assert not list(locations.reports_dir.glob("*-audit/intruders.csv"))


def test_protected_folders_are_left_out(
    media: MediaFactory, locations: Locations
) -> None:
    """A protected folder is never changed: its intruders are never proposed."""
    _tree(media, locations)
    runtime = make_runtime(locations, {"folders": {"protected": ["C:\\Kept"]}})
    names = sorted(item.path.name for item in current_intruders(runtime))
    assert names == ["b.zip", "c.pdf"]


def test_picked_files_are_quarantined_and_undo_brings_them_back(
    cli: CliRunner, media: MediaFactory, locations: Locations
) -> None:
    """Only the zips of Photos; the pdf is not picked; undo restores the bytes."""
    photos = _tree(media, locations)
    runtime = make_runtime(locations)
    pick = IntruderPick(frozenset({".zip"}), (photos,))
    saved = set_intruders_aside(runtime, pick)
    assert [(file.path, file.found_by) for file in saved] == [
        ("C:\\Photos\\b.zip", FOUND_BY)
    ]
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert not (photos / "b.zip").exists()
    assert (photos / "Trip" / "c.pdf").exists()
    assert (locations.data_dir / "c" / "Kept" / "x.zip").exists()
    (moved,) = locations.quarantine_dir.rglob("b.zip")
    assert moved.read_bytes() == _ZIP
    assert run(cli, "undo").exit_code == 0
    assert (photos / "b.zip").read_bytes() == _ZIP
    assert not list(locations.quarantine_dir.rglob("b.zip"))


def test_a_file_moved_since_it_was_picked_is_skipped_and_said(
    cli: CliRunner, media: MediaFactory, locations: Locations
) -> None:
    """The user moved the pdf in Explorer: the clean leaves it; the zip goes."""
    photos = _tree(media, locations)
    runtime = make_runtime(locations)
    saved = set_intruders_aside(
        runtime, IntruderPick(frozenset({".zip", ".pdf"}), (photos,))
    )
    assert len(saved) == 2
    assert read_decisions(locations.reports_dir / "decisions.json").chosen == saved
    (photos / "Trip" / "c.pdf").rename(photos / "c-moved.pdf")
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "Skipped (left untouched) │ 1" in " ".join(result.output.split())
    assert (photos / "c-moved.pdf").read_bytes() == _PDF
    assert not (photos / "b.zip").exists()


def test_nothing_picked_saves_nothing(
    media: MediaFactory, locations: Locations
) -> None:
    """No extension and no folder: no file is set aside."""
    _tree(media, locations)
    assert set_intruders_aside(make_runtime(locations), IntruderPick()) == ()
