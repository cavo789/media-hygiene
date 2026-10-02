"""Where `classify` writes its plan, workbook and report, and when it cannot."""

from __future__ import annotations

import errno
from typing import TYPE_CHECKING

from media_hygiene.report.classify_writer import ClassifyReportWriter
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.classify.plan_file import ClassifyPlan
    from media_hygiene.paths.locations import Locations


def test_without_a_reports_mount_the_proposals_stay_on_screen(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A workbook in a folder the container forgets would be lost work: none."""
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert "Already in place" in result.output
    assert ":/reports" in result.output
    assert "classify.xlsx" not in result.output


def test_a_report_that_cannot_be_written_is_a_warning(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The proposals are on screen; the message names the folder and the fix."""

    def denied(_writer: ClassifyReportWriter, _plan: ClassifyPlan) -> Path:
        raise PermissionError(errno.EACCES, "Permission denied", "/reports/x")

    monkeypatch.setattr(ClassifyReportWriter, "write", denied)
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert "Already in place" in result.output
    assert "could not be written" in result.output
    assert "--user" in result.output
    assert list(locations.reports_dir.glob("*-classify/plan.json"))


def test_two_runs_in_the_same_second_get_two_folders(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A run never overwrites the workbook of another one."""
    monkeypatch.setattr("media_hygiene.report.folders._STAMP_FORMAT", "fixed")
    assert run(cli, "classify").exit_code == 0
    assert run(cli, "classify").exit_code == 0
    folders = sorted(path.name for path in locations.reports_dir.glob("*-classify*"))
    assert folders == ["fixed-classify", "fixed-classify-2"]
