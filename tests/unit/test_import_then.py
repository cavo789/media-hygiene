"""After an import: the chain of `[imports] then` (0475)."""

from __future__ import annotations

import os
from datetime import UTC, datetime
from typing import TYPE_CHECKING

import pytest
from typer.testing import CliRunner

from media_hygiene.cli.app import build_app
from media_hygiene.config.import_settings import ImportSettings, ImportStep
from media_hygiene.config.loader import load_settings
from media_hygiene.services.import_end import PHONE_END, new_files
from media_hygiene.services.phone_plan import PHONE_PLAN
from tests.support.cli import point_mounts

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.paths.locations import Locations


def test_the_audit_comes_first_while_another_step_is_on() -> None:
    """Order fixed, each step once, audit added; empty stays empty."""
    settings = ImportSettings.model_validate({"then": ["tags", "tags"]})
    assert settings.then == (ImportStep.AUDIT, ImportStep.TAGS)
    assert ImportSettings.model_validate({"then": []}).then == ()
    assert ImportSettings().then == tuple(ImportStep)


def test_the_toggles_are_read_back_from_config_toml(locations: Locations) -> None:
    """`[imports] then` written in config.toml, read back."""
    locations.config_dir.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text('[imports]\nthen = ["audit"]\n', encoding="utf-8")
    assert load_settings(locations).settings.imports.then == (ImportStep.AUDIT,)


@pytest.fixture
def runner(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """A runner whose mount points are the test's folders."""
    point_mounts(locations, monkeypatch)
    locations.data_dir.mkdir(parents=True, exist_ok=True)
    return CliRunner()


def test_the_plan_ends_with_the_steps_switched_on(
    runner: CliRunner, locations: Locations
) -> None:
    """A disabled step is never listed: `mh` runs only what the plan says."""
    locations.config_dir.mkdir(parents=True, exist_ok=True)
    locations.config_file.write_text('[imports]\nthen = ["places"]\n', encoding="utf-8")
    day = datetime.now(UTC).strftime("%Y%m%d")
    listing = f"Camera/IMG_{day}_1.jpg\t10\t2026-10-29T10:00:00Z\n"
    result = runner.invoke(build_app(), [PHONE_PLAN, "--since", "all"], input=listing)
    lines = result.stdout.splitlines()
    assert lines[0].startswith("new\tCamera/IMG_")
    assert lines[1:] == ["then\taudit", "then\tplaces"]


def test_a_bad_period_is_said_without_a_traceback(runner: CliRunner) -> None:
    """--since yesterday: refused, its tip shown."""
    result = runner.invoke(build_app(), [PHONE_PLAN, "--since", "yesterday"], input="")
    assert result.exit_code != 0
    assert "--since takes today" in result.output


def test_the_new_files_are_those_of_the_period(tmp_path: Path) -> None:
    """The import's folder: media files of the period only."""
    old = tmp_path / "Camera" / "DSC1.JPG"
    old.parent.mkdir()
    old.write_bytes(b"x")
    stamp = datetime(2020, 1, 1, tzinfo=UTC).timestamp()
    os.utime(old, (stamp, stamp))
    new = tmp_path / "Camera" / "IMG_20261029_1.jpg"
    new.write_bytes(b"x")
    (tmp_path / "notes.txt").write_text("x", encoding="utf-8")
    assert new_files(tmp_path, datetime(2026, 10, 1, tzinfo=UTC).date()) == (new,)
    assert new_files(tmp_path, None) == (old, new)


def test_phone_end_proposes_the_slideshow(
    runner: CliRunner, locations: Locations
) -> None:
    """No index yet: nothing to name, nothing said, no failure."""
    folder = locations.data_dir / "c" / "Photos" / "Phone"
    folder.mkdir(parents=True)
    (folder / "IMG_20261029_1.jpg").write_bytes(b"x")
    result = runner.invoke(
        build_app(), [PHONE_END, "--folder", "C:\\Photos\\Phone", "--since", "all"]
    )
    assert result.exit_code == 0, result.output


def test_phone_end_copies_sets_aside_only_and_says_so(
    runner: CliRunner, locations: Locations
) -> None:
    """0480: `--copies` runs alone, right after the audit; no slideshow line."""
    folder = locations.data_dir / "c" / "Photos" / "Phone"
    folder.mkdir(parents=True)
    (folder / "IMG_20261029_1.jpg").write_bytes(b"x")
    result = runner.invoke(
        build_app(),
        [PHONE_END, "--folder", "C:\\Photos\\Phone", "--since", "all", "--copies"],
    )
    assert result.exit_code == 0, result.output
    assert "set aside" in result.output
    assert "All done" not in result.output


def test_the_default_order_puts_copies_before_tags() -> None:
    """Audit, copies, bursts, tags, places (0480)."""
    assert ImportSettings().then == (
        ImportStep.AUDIT,
        ImportStep.COPIES,
        ImportStep.BURSTS,
        ImportStep.TAGS,
        ImportStep.PLACES,
    )
