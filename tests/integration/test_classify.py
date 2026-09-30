"""`classify` on the demo tree: after an audit it decodes nothing, changes nothing."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.classify.workbook.reader import read_edits
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.classify import ClassifyService
from tests.support.cli import run
from tests.support.demo import build_demo
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def snapshot(root: Path) -> dict[str, int]:
    """Every file of the data folder, with its modification time."""
    return {
        str(path): path.stat().st_mtime_ns for path in root.rglob("*") if path.is_file()
    }


def test_after_an_audit_classify_decodes_nothing_and_changes_nothing(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The index answers everything; the data folder is left as it was."""
    build_demo(locations.data_dir)
    runtime = make_runtime(locations)
    AuditService(runtime, NullProgress()).run()
    before = snapshot(locations.data_dir)

    def forbidden(*_args: object) -> None:
        raise AssertionError

    for name in ("inspect_image", "read_image_metadata", "probe_video"):
        monkeypatch.setattr(f"media_hygiene.scan.file_check.{name}", forbidden)
    result = ClassifyService(runtime, NullProgress()).run()
    assert result.classification.proposals
    assert snapshot(locations.data_dir) == before
    assert result.duplicates > 0  # the demo still holds copies: clean first


def test_the_command_scopes_years_and_targets(cli: CliRunner) -> None:
    """`--year` limits the proposals; `--target` must be mounted; a bad year is said."""
    assert run(cli, "audit").exit_code == 0  # its digests tell the duplicates
    everything = run(cli, "classify")
    assert everything.exit_code == 0, everything.output
    assert "Already in place" in everything.output
    assert "run 'clean' first" in everything.output
    one_year = run(cli, "classify", "--year", "2019", "--target", "C:\\Tri")
    assert one_year.exit_code == 0, one_year.output
    assert run(cli, "classify", "--year", "last year").exit_code == 1
    assert run(cli, "classify", "--target", "Z:\\nowhere").exit_code == 1


def test_the_plan_workbook_and_report_are_written_to_reports(
    cli: CliRunner, locations: Locations
) -> None:
    """One folder per run: `plan.json`, the workbook, the report, a page per year."""
    assert run(cli, "audit").exit_code == 0
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert "classify.xlsx" in result.output
    (folder,) = locations.reports_dir.glob("*-classify")
    plan = ClassifyPlan.model_validate_json((folder / "plan.json").read_text("utf-8"))
    assert read_edits(folder / "classify.xlsx", plan).files == {}
    report = (folder / "report.html").read_text("utf-8")
    years = {row.values.year for row in plan.rows if row.values}
    assert any(f'href="{year}.html"' in report for year in years)
    assert list(folder.glob("thumbs/*.jpg"))
    first = plan.rows[0]
    assert first.path.startswith("C:\\")


def test_rules_from_config_toml_are_applied_and_checked(
    cli: CliRunner, locations: Locations
) -> None:
    """Overlapping trips are a warning; each rule's files are counted by its name."""
    trips = (("Italy", "2019-07-01..2019-07-31"), ("Rome", "2019-07-10..2019-07-12"))
    locations.config_file.write_text(
        "".join(
            f'[[classify.rules]]\nname = "{name}"\nmatch = "date_range"\n'
            f'dates = "{dates}"\ncategory = "Trips/{name}"\n\n'
            for name, dates in trips
        )
        + '[[classify.rules]]\nname = "Folders"\nmatch = "existing_folder"\n',
        "utf-8",
    )
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    assert "'Italy' and 'Rome' overlap" in result.output
    assert "Folders" in result.output
