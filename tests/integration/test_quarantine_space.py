"""`clean`, photos on E: and quarantine on C:: told, or refused untouched."""

from __future__ import annotations

from types import SimpleNamespace
from typing import TYPE_CHECKING

from media_hygiene.paths.mounts import MountTable
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

GB = 1024**3


def on_two_drives(
    locations: Locations, monkeypatch: pytest.MonkeyPatch, free: int
) -> None:
    """Docker Desktop's mount table: data from E:, quarantine from C:, `free` bytes."""
    table = MountTable(
        frozenset(),
        (
            (locations.data_dir, "E:\\"),
            (locations.quarantine_dir, "C:\\Users\\me\\media-hygiene\\quarantine"),
        ),
    )
    monkeypatch.setattr(MountTable, "current", classmethod(lambda _cls: table))
    monkeypatch.setattr("shutil.disk_usage", lambda _folder: SimpleNamespace(free=free))


def tree(folder: Path) -> dict[str, bytes]:
    """Every file below a folder, with its bytes."""
    return {
        str(path.relative_to(folder)): path.read_bytes()
        for path in sorted(folder.rglob("*"))
        if path.is_file()
    }


def test_short_of_room_nothing_moves_and_nothing_is_journaled(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Refused before the confirmation: data, journal, quarantine as before."""
    on_two_drives(locations, monkeypatch, free=0)
    before = tree(locations.data_dir)
    result = run(cli, "clean", "--yes")
    assert result.exit_code == 1, result.output
    text = " ".join(result.output.split())
    assert "Not enough room on C: for the quarantine" in text
    assert "from E:" in text
    assert tree(locations.data_dir) == before
    assert not any(locations.journal_dir.iterdir())
    assert not any(locations.quarantine_dir.iterdir())


def test_with_room_the_line_comes_then_the_clean(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Enough room: the line names both drives, then the copies are set aside."""
    on_two_drives(locations, monkeypatch, free=500 * GB)
    result = run(cli, "clean", "--yes")
    assert result.exit_code == 0, result.output
    text = " ".join(result.output.split())
    assert (
        "will be copied from E: to the quarantine on C: (500.0 GB free there)" in text
    )
    assert text.index("will be copied from E:") < text.index("─ Clean ─")
    assert any(locations.quarantine_dir.rglob("*.jpg"))
