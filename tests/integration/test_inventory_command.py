"""`media-hygiene inventory` on the command line, and what it refuses."""

from __future__ import annotations

import sqlite3
from typing import TYPE_CHECKING

import pytest

from media_hygiene.constants import InventoryFormat
from media_hygiene.errors import MountError
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.services.inventory import export_inventory
from tests.support.cli import run
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_audit_then_inventory(cli: CliRunner, locations: Locations) -> None:
    """After an audit, the export names its file and the date of each root."""
    assert run(cli, "audit").exit_code == 0
    result = run(cli, "inventory")
    assert result.exit_code == 0, result.output
    output = " ".join(result.output.split())
    assert "files written:" in output
    assert "Last complete audit (UTC)" in output
    assert list(locations.reports_dir.glob("*-inventory/inventory.xlsx"))
    assert run(cli, "inventory", "--format", "csv").exit_code == 0
    assert list(locations.reports_dir.glob("*-inventory*/inventory.csv"))


def test_before_any_audit_the_export_asks_for_one(
    cli: CliRunner, locations: Locations
) -> None:
    """No index yet: a message and a tip, no traceback, and no index created."""
    result = run(cli, "inventory")
    assert result.exit_code != 0
    output = " ".join(result.output.split())
    assert "nothing to export yet" in output
    assert "Run 'audit' first" in output
    assert not locations.index_file.exists()


def test_an_empty_index_is_refused(locations: Locations) -> None:
    """An index without any file (an audit of an empty folder) has nothing to say."""
    sqlite3.connect(locations.index_file).close()
    with pytest.raises(MountError, match="nothing to export"):
        export_inventory(make_runtime(locations), InventoryFormat.XLSX)


def test_a_damaged_index_is_refused(locations: Locations) -> None:
    """A file that is not SQLite: the message names it, the tip says to delete it."""
    locations.index_file.write_bytes(b"not a database, not at all" * 100)
    with pytest.raises(MountError, match="cannot be read") as caught:
        export_inventory(make_runtime(locations), InventoryFormat.XLSX)
    assert caught.value.tip is not None
    assert "Delete it" in caught.value.tip


@pytest.mark.parametrize("missing", [MountKind.CACHE, MountKind.REPORTS])
def test_both_mounts_are_needed(tmp_path: Path, missing: MountKind) -> None:
    """Without /cache nothing to read; without /reports nowhere to keep the file."""
    locations = make_locations(tmp_path, missing)
    if missing is MountKind.REPORTS:
        sqlite3.connect(locations.index_file).close()
    with pytest.raises(MountError):
        export_inventory(make_runtime(locations), InventoryFormat.XLSX)
