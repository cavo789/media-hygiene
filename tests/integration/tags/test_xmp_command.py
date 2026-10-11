"""`media-hygiene xmp`: dry run, write, again, undo; protected, copies, refusals."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.tags.xmp_doc import items, parse
from media_hygiene.tags.xmp_merge import SUBJECT
from media_hygiene.tags.xmp_owner import is_ours
from tests.support.cli import run
from tests.support.sidecars import DARKTABLE

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

# 19 photos: 3 in the protected 2022 folder, 2 identical copies, 14 written.
WRITTEN = 14


@pytest.fixture
def tagged(cli: CliRunner, locations: Locations) -> CliRunner:
    """The tree tagged with its folder and date words, 2022 protected."""
    config = locations.config_dir / "config.toml"
    text = config.read_text("utf-8") + 'xmp_sources = ["folder", "date"]\n'
    text += "\n[folders]\nprotected = ['C:\\Photos\\2022']\n"
    config.write_text(text, "utf-8")
    assert run(cli, "tags", "--no-describe").exit_code == 0
    return cli


def _said(cli: CliRunner, *args: str) -> str:
    """Run a command that must succeed; its output on one line."""
    result = run(cli, *args)
    assert result.exit_code == 0, result.output
    return " ".join(result.output.split())


def _sidecars(locations: Locations) -> list[Path]:
    """Every `.xmp` file of the photos."""
    return sorted(locations.data_dir.rglob("*.xmp"))


def test_dry_run_write_again_then_undo(tagged: CliRunner, locations: Locations) -> None:
    """Nothing before --apply; ours created, darktable's merged; undo puts all back."""
    dcim = locations.data_dir / "c" / "Photos" / "DCIM"
    darktable = dcim / "IMG_snow_1.xmp"
    darktable.write_text(DARKTABLE, "utf-8")
    shown = _said(tagged, "xmp")
    assert f"{WRITTEN} sidecars to write: {WRITTEN - 1} new, 1 with the words" in shown
    assert "3 files of protected folders" in shown
    assert "2 files have an identical copy" in shown
    assert "add --apply" in shown
    assert "... and 4 more." in shown
    one_folder = _said(tagged, "xmp", "--path", "C:\\Photos\\2022")
    assert "0 sidecars to write" in one_folder
    assert "3 files of protected folders" in one_folder
    assert _sidecars(locations) == [darktable]
    written = _said(tagged, "xmp", "--apply")
    assert f"{WRITTEN} sidecars written and read back" in written
    created = dcim / "IMG_cake_0.jpg.xmp"
    assert is_ours(created)
    assert "2023" in items(parse(created.read_bytes()).find(SUBJECT))
    merged = darktable.read_text("utf-8")
    assert "darktable:history" in merged
    assert "Mon texte" in merged
    assert not (dcim / "IMG_snow_1.jpg.xmp").exists()
    assert len(_sidecars(locations)) == WRITTEN
    assert not list((locations.data_dir / "c" / "Photos" / "2022").glob("*.xmp"))
    again = _said(tagged, "xmp", "--apply")
    assert "Nothing to write." in again
    assert f"{WRITTEN} sidecars hold these words already" in again
    assert "Sidecars" in _said(tagged, "history")
    run_id = written.split("undo ")[1].split()[0].strip("'")
    undone = _said(tagged, "undo", run_id, "--yes")
    assert "Traceback" not in undone
    assert _sidecars(locations) == [darktable]
    assert darktable.read_text("utf-8") == DARKTABLE


def test_a_sidecar_edited_since_is_kept_by_undo(
    tagged: CliRunner, locations: Locations
) -> None:
    """Undo never removes a sidecar changed in another application."""
    written = _said(tagged, "xmp", "--apply")
    run_id = written.split("undo ")[1].split()[0].strip("'")
    edited = locations.data_dir / "c" / "Photos" / "DCIM" / "IMG_cake_0.jpg.xmp"
    edited.write_bytes(edited.read_bytes().replace(b"2023", b"2024"))
    undone = _said(tagged, "undo", run_id, "--yes")
    assert "changed since" in undone
    assert _sidecars(locations) == [edited]


def test_refusals(
    tagged: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A sidecar that is not XMP is listed and left; no journal, nothing written."""
    broken = locations.data_dir / "c" / "Photos" / "DCIM" / "IMG_cake_1.jpg.xmp"
    broken.write_text("<x:xmpmeta", "utf-8")
    shown = _said(tagged, "xmp")
    assert "IMG_cake_1.jpg.xmp: not an XMP file this tool can read" in shown
    monkeypatch.delenv("MEDIA_HYGIENE_JOURNAL_DIR")
    refused = run(tagged, "xmp", "--apply")
    assert refused.exit_code == 1
    assert "No journal mount" in refused.output
    assert _sidecars(locations) == [broken]
