"""`media-hygiene sort` from the command line: what it reads, asks, does and says."""

from __future__ import annotations

import shutil
from types import SimpleNamespace
from typing import TYPE_CHECKING

from tests.support.cli import run
from tests.support.sorting import PARTY, build_library, name_first_event

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def classified(cli: CliRunner, locations: Locations) -> Path:
    """The library alone, classified; its workbook, one event named."""
    shutil.rmtree(locations.data_dir)
    build_library(locations.data_dir)
    assert run(cli, "classify").exit_code == 0
    (workbook,) = locations.reports_dir.glob("*-classify/classify.xlsx")
    name_first_event(workbook)
    return workbook


def test_sort_shows_what_it_read_moves_and_proves(
    cli: CliRunner, locations: Locations
) -> None:
    """The edits read, the summary, the moves, the proof, how to undo."""
    classified(cli, locations)
    result = run(cli, "sort", "--yes")
    assert result.exit_code == 0, result.output
    assert "1 edit read; workbook saved on" in result.output
    assert "Files to move" in result.output
    assert "🛟 Each file is moved, never over another one nor deleted" in result.output
    assert "Nothing lost: " in result.output
    assert "manifest.json" in result.output
    assert "undo" in result.output
    assert not (locations.data_dir / PARTY).exists()
    again = run(cli, "sort", "--yes")
    assert again.exit_code == 0
    assert "Moved by an earlier run" in again.output
    assert "Nothing to move" in again.output
    history = run(cli, "history").output
    assert " sort " in history
    undo = run(cli, "undo")
    assert undo.exit_code == 0, undo.output
    assert (locations.data_dir / PARTY).is_dir()


def test_a_workbook_is_found_by_its_path_and_its_plan_by_id(
    cli: CliRunner, locations: Locations, tmp_path: Path
) -> None:
    """A copy edited elsewhere under /data finds its plan.json in /reports."""
    workbook = classified(cli, locations)
    copy = locations.data_dir / "d" / "edited.xlsx"
    copy.parent.mkdir(parents=True)
    shutil.copy2(workbook, copy)
    (workbook.parent / "~$classify.xlsx").write_text("lock", encoding="utf-8")
    result = run(cli, "sort", "--keep-empty-folders", "--yes", "D:\\edited.xlsx")
    assert result.exit_code == 0, result.output
    assert (locations.data_dir / PARTY / "Thumbs.db").is_file()
    missing = run(cli, "sort", str(tmp_path / "nowhere.xlsx"))
    assert missing.exit_code == 1
    assert "was not found" in " ".join(missing.output.split())
    opened = run(cli, "sort", "--yes", str(workbook))
    assert "open in Excel" in " ".join(opened.output.split())


def test_a_foreign_plan_is_refused(cli: CliRunner, locations: Locations) -> None:
    """plan.json replaced by another run's: the workbook's plan is nowhere."""
    workbook = classified(cli, locations)
    plan = workbook.parent / "plan.json"
    assert run(cli, "classify").exit_code == 0
    other = max(locations.reports_dir.glob("*-classify*/plan.json"))
    shutil.copy2(other, plan)
    other.unlink()
    result = run(cli, "sort", "--yes", str(workbook))
    assert result.exit_code == 1
    assert "is not in /reports" in " ".join(result.output.split())


def test_without_a_terminal_sort_asks_for_yes(
    cli: CliRunner, locations: Locations
) -> None:
    """No terminal to confirm in: refused, nothing moved."""
    classified(cli, locations)
    result = run(cli, "sort")
    assert result.exit_code == 1
    assert "--yes" in result.output
    assert (locations.data_dir / PARTY).is_dir()


def test_without_reports_or_workbook_sort_says_what_to_do(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No classify run yet, then no reports mount at all."""
    none = run(cli, "sort")
    assert none.exit_code == 1
    assert "Run 'classify' first" in none.output
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    unmounted = run(cli, "sort")
    assert unmounted.exit_code == 1
    assert "No reports mount" in unmounted.output
    assert locations.reports_dir.is_dir()


def test_sort_help_lists_its_options(cli: CliRunner) -> None:
    """Every option has its help."""
    result = run(cli, "sort", "--help")
    assert "--keep-empty-folders" in result.output
    assert "--yes" in result.output


def test_a_no_at_the_question_moves_nothing(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Asked in a terminal, anything but yes changes nothing."""
    classified(cli, locations)
    terminal = SimpleNamespace(stdin=SimpleNamespace(isatty=lambda: True))
    monkeypatch.setattr("media_hygiene.cli.cmd_sort.sys", terminal)
    monkeypatch.setattr(
        "media_hygiene.console.output.Output.confirm", lambda _self, _question: False
    )
    result = run(cli, "sort")
    assert result.exit_code == 0, result.output
    assert "Nothing was changed" in result.output
    assert (locations.data_dir / PARTY).is_dir()
