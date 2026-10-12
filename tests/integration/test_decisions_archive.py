"""`clean --decisions` archives the applied file, which applies again after undo."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

RAFALE = "C:\\Family Photos\\Rafale"
BLURRED = "c/Family Photos/Rafale/IMG_202.jpg"


def write_decisions(locations: Locations, discarded: str) -> Path:
    """The decisions file `review` writes: one shot of the demo burst set aside."""
    kept = [f"{RAFALE}\\IMG_20{rank}.jpg" for rank in (0, 1, 3)]
    bursts = [{"kept": kept, "discarded": [discarded]}]
    decisions = {"version": 1, "roots": ["C:\\", "D:\\"], "bursts": bursts}
    target = locations.reports_dir / "decisions.json"
    target.write_text(json.dumps(decisions))
    return target


def test_applied_file_is_archived_then_applied_again_after_undo(
    cli: CliRunner, locations: Locations
) -> None:
    """Renamed beside itself; after undo, the archive moves the same shot again."""
    target = write_decisions(locations, f"{RAFALE}\\IMG_202.jpg")
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert not target.exists()
    (archive,) = locations.reports_dir.glob("decisions.applied-*.json")
    said = "".join(result.output.split())
    assert "isapplied:archivedas" in said
    assert f"clean--decisions{archive.name}" in said
    assert run(cli, "undo").exit_code == 0
    assert (locations.data_dir / BLURRED).is_file()
    again = run(cli, "clean", "--yes", "--decisions", archive.name)
    assert again.exit_code == 0, again.output
    assert not (locations.data_dir / BLURRED).exists()
    assert not archive.exists()


def test_refused_file_stays(cli: CliRunner, locations: Locations) -> None:
    """Nothing cleaned, nothing archived."""
    target = write_decisions(locations, "C:\\elsewhere.jpg")
    assert run(cli, "clean", "--yes", "--decisions", "decisions.json").exit_code == 1
    assert target.is_file()
    assert not list(locations.reports_dir.glob("decisions.applied-*.json"))


def test_a_failed_rename_only_warns(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The clean is done: a read-only reports folder is a warning, not an error."""
    target = write_decisions(locations, f"{RAFALE}\\IMG_202.jpg")

    def refuse(_self: Path, _new: Path) -> Path:
        raise PermissionError(13, "Permission denied")

    monkeypatch.setattr(type(target), "rename", refuse)
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "could not be archived (Permission denied)" in result.output
    assert target.is_file()


def test_a_rename_not_seen_on_disk_is_not_announced(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read back: the file still there is never called archived."""
    target = write_decisions(locations, f"{RAFALE}\\IMG_202.jpg")
    monkeypatch.setattr(type(target), "rename", lambda self, _new: self)
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    assert "could not be archived." in result.output
    assert "is applied" not in result.output
