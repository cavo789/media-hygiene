"""`purge --to` (0306): two drive quarantines archived, proven, erased; then undone."""

from __future__ import annotations

import json
import shutil
from typing import TYPE_CHECKING

from media_hygiene.actions.purged import purge_dates
from media_hygiene.cli.app import build_app
from tests.integration.test_quarantine_drives import clean, digests, files, mount
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_archive_keeps_each_drive_apart_and_undo_brings_it_all_back(
    cli: CliRunner,
    locations: Locations,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """C: and D: land in <target>/<run>/C and /D, byte for byte; copy back + undo."""
    tmp_path = locations.data_dir.parent  # the test's own folder
    own = mount(locations, monkeypatch, d_quarantine=True)
    before = digests(locations.data_dir)
    run_id = clean(cli, locations)
    on_c = digests(locations.quarantine_dir / run_id)
    on_d = digests(own / run_id)
    target = tmp_path / "nas"
    result = run(cli, "purge", "--to", str(target), "--yes")
    assert result.exit_code == 0, result.output
    assert digests(target / run_id / "C") == on_c
    assert digests(target / run_id / "D") == on_d
    assert not (locations.quarantine_dir / run_id).exists()
    assert not (own / run_id).exists()
    text = " ".join(result.output.split())
    assert f"{len(on_c) + len(on_d)} files" in text
    assert "undo" in text
    record = locations.journal_dir / f"{run_id}.archived.json"
    assert json.loads(record.read_text(encoding="utf-8"))["run"] == run_id
    assert run_id in purge_dates(locations.journal_dir, [run_id])  # purged for readers
    shutil.copytree(target / run_id / "C", locations.quarantine_dir / run_id)
    shutil.copytree(target / run_id / "D", own / run_id)
    result = run(cli, "undo", run_id, "--yes")
    assert result.exit_code == 0, result.output
    assert digests(locations.data_dir) == before


def test_a_failed_copy_erases_nothing(
    cli: CliRunner,
    locations: Locations,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """The disk fills up midway: the run stays whole, no record written."""
    tmp_path = locations.data_dir.parent  # the test's own folder
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    kept = files(locations.quarantine_dir / run_id)
    calls = 0

    def full_disk(source: Path, copy: Path) -> None:
        nonlocal calls
        calls += 1
        if calls > 1:
            raise OSError(28, "No space left on device")
        copy.write_bytes(source.read_bytes())

    monkeypatch.setattr(shutil, "copy2", full_disk)
    result = run(cli, "purge", "--to", str(tmp_path / "nas"), "--yes")
    assert result.exit_code != 0
    assert "No space left" in " ".join(result.output.split())
    assert files(locations.quarantine_dir / run_id) == kept
    assert not (locations.journal_dir / f"{run_id}.archived.json").exists()
    assert not purge_dates(locations.journal_dir, [run_id])


def test_not_enough_room_is_refused_before_copying(
    cli: CliRunner,
    locations: Locations,
    monkeypatch: pytest.MonkeyPatch,
) -> None:
    """Free space is checked first: nothing copied, nothing erased."""
    tmp_path = locations.data_dir.parent  # the test's own folder
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    usage = shutil.disk_usage(tmp_path)
    monkeypatch.setattr(shutil, "disk_usage", lambda _path: usage._replace(free=0))
    result = run(cli, "purge", "--to", str(tmp_path / "nas"), "--yes")
    assert result.exit_code != 0
    assert not (tmp_path / "nas").exists()
    assert (locations.quarantine_dir / run_id).is_dir()


def test_a_target_inside_a_tool_or_photo_folder_is_refused(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The quarantine itself, or a photo folder, is never an archive."""
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    for inside in (locations.quarantine_dir / "copy", locations.data_dir / "c" / "x"):
        result = run(cli, "purge", "--to", str(inside), "--yes")
        assert result.exit_code != 0
        assert "one inside the other" in " ".join(result.output.split())
    assert (locations.quarantine_dir / run_id).is_dir()


def test_the_hint_shows_before_the_question_only_without_to_or_yes(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Declining after the hint changes nothing; --yes hides it."""
    mount(locations, monkeypatch, d_quarantine=True)
    run_id = clean(cli, locations)
    asked = cli.invoke(build_app(), ["purge"], input="n\n", catch_exceptions=False)
    assert "--to <folder>" in " ".join(asked.output.split())
    assert (locations.quarantine_dir / run_id).is_dir()
    done = run(cli, "purge", "--yes")
    assert "--to <folder>" not in " ".join(done.output.split())
