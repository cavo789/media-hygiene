"""`classify` says what it carried over and what it could not; a bad file stops it."""

from __future__ import annotations

from typing import TYPE_CHECKING

from tests.support.carrying import WEDDING, build_day, edit, final, rename
from tests.support.cli import run

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def _workbooks(locations: Locations) -> list[Path]:
    """The workbooks of every classify run, oldest first."""
    return sorted(locations.reports_dir.glob("*-classify*/classify.xlsx"))


def test_the_console_and_the_report_list_the_edits(
    cli: CliRunner, locations: Locations
) -> None:
    """Carried, with the date and the workbook; an edit left behind is listed."""
    build_day(locations.data_dir)
    assert run(cli, "classify").exit_code == 0
    edit(
        _workbooks(locations)[0],
        final("M1.jpg", "2018/Gone") | rename("Mariage", "Wedding"),
    )
    (locations.data_dir / WEDDING / "M1.jpg").unlink()
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert "1 edit carried over from the workbook saved on" in result.output
    assert "1 edit found no place in the new proposal" in result.output
    assert "M1.jpg: '2018/Gone' (the file is gone)" in result.output
    report = max(locations.reports_dir.glob("*-classify*/report.html"))
    page = report.read_text(encoding="utf-8")
    assert "Edits carried over" in page
    assert "2018/Gone" in page


def test_no_carry_over_and_a_workbook_that_is_not_there(
    cli: CliRunner, locations: Locations
) -> None:
    """`--no-carry-over` is silent; `--carry-over` of a missing file stops at once."""
    build_day(locations.data_dir)
    run(cli, "classify")
    edit(_workbooks(locations)[0], rename("Mariage", "Wedding"))
    fresh = run(cli, "classify", "--no-carry-over")
    assert fresh.exit_code == 0, fresh.output
    assert "carried over" not in fresh.output
    missing = run(cli, "classify", "--carry-over", "missing.xlsx")
    assert missing.exit_code != 0
    assert "missing.xlsx was not found" in missing.output
    assert len(_workbooks(locations)) == 2


def test_an_unreadable_latest_workbook_stops_classify(
    cli: CliRunner, locations: Locations
) -> None:
    """Its edits would be buried under a newer run: nothing is written."""
    build_day(locations.data_dir)
    run(cli, "classify")
    (latest,) = _workbooks(locations)
    latest.write_text("not a workbook", encoding="utf-8")
    result = run(cli, "classify")
    assert result.exit_code != 0
    assert "--no-carry-over" in result.output
    assert len(_workbooks(locations)) == 1
