"""clean --tier near-all: every near duplicate shown in a report before the question."""

from __future__ import annotations

import csv
from typing import TYPE_CHECKING

from media_hygiene.cli import cmd_clean
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

WHATSAPP = "IMG-20210705-WA0001.jpg"


def decline(monkeypatch: pytest.MonkeyPatch) -> None:
    """Answer 'no' to the confirmation, as a person at a terminal would."""
    monkeypatch.setattr(cmd_clean, "confirm_clean", lambda *_args: False)


def test_the_report_is_linked_before_the_question(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """An audit report is written first and named; declining changes nothing."""
    decline(monkeypatch)
    result = run(cli, "clean", "--tier", "near-all")
    assert result.exit_code == 0, result.output
    joined = "".join(result.output.split())
    assert "lookatthembeforeanswering" in joined
    assert joined.endswith("near.html(Ctrl+clickopensit).Nothingwaschanged.")
    assert "Nothing was changed." in result.output
    report = next(locations.reports_dir.glob("*-audit/report.html"))
    assert WHATSAPP in report.read_text()
    assert not list(locations.reports_dir.glob("*-clean"))


def test_nothing_is_written_without_a_question(
    cli: CliRunner, locations: Locations
) -> None:
    """--yes: nobody looks, so only the report of the clean is written."""
    assert run(cli, "clean", "--yes", "--tier", "near-all").exit_code == 0
    assert not list(locations.reports_dir.glob("*-audit"))
    assert list(locations.reports_dir.glob("*-clean"))


def test_a_plain_clean_writes_no_report_first(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Without the tier, no near duplicate moves: nothing to look at first."""
    decline(monkeypatch)
    result = run(cli, "clean")
    assert "look at them before answering" not in " ".join(result.output.split())
    assert not list(locations.reports_dir.glob("*-audit"))


def test_plan_csv_lists_the_near_duplicates(
    cli: CliRunner, locations: Locations
) -> None:
    """The audit's plan.csv names each near copy, moved only with the tier."""
    assert run(cli, "audit").exit_code == 0
    folder = next(locations.reports_dir.glob("*-audit"))
    text = (folder / "plan.csv").read_text(encoding="utf-8-sig")
    rows = list(csv.reader(text.splitlines()))
    near = [row for row in rows if row[3] == "move with --tier near-all"]
    assert any(row[4].endswith(WHATSAPP) for row in near)
    assert all(row[0] and not row[1] for row in near)  # a group, no SHA-256
    kept = [row for row in rows if row[7].startswith("Near duplicate:")]
    assert {row[0] for row in kept} == {row[0] for row in near}
    assert rows[0][8] == "Near-duplicate level"
    assert all(row[8].startswith("To check:") for row in kept)


def test_the_report_has_contents_and_a_near_page(
    cli: CliRunner, locations: Locations
) -> None:
    """Each section shown has an entry; near.html holds the near duplicates alone."""
    assert run(cli, "audit").exit_code == 0
    folder = next(locations.reports_dir.glob("*-audit"))
    report = (folder / "report.html").read_text()
    for anchor in ("groups", "near", "bursts", "broken"):
        assert f'<a href="#{anchor}">' in report
        assert f'<h2 id="{anchor}">' in report
    assert '<a href="#untouched">' not in report  # an audit leaves nothing untouched
    assert '<a href="near.html">' in report
    page = (folder / "near.html").read_text()
    assert WHATSAPP in page
    assert 'class="toc"' not in page  # one section only: no contents needed
    assert 'id="bursts"' not in page
    assert 'target="_blank"' in page  # each photo opens in full, in a new tab
    assert 'href="file:///C:/' in page
    assert "0 sure, 1 to check" in page
    assert "To check: compare the copies" in page
    assert "with the groups above: 100 % of the space" in page
    assert '<details class="sure">' not in page  # nothing folded


def test_the_french_near_page_counts_each_noun_on_its_own(
    cli: CliRunner, locations: Locations
) -> None:
    """`0 sûr, 1 à vérifier`: the sure groups agree with their own number."""
    install(Locale.FR)  # the report follows the installed language
    assert run(cli, "audit").exit_code == 0
    folder = next(locations.reports_dir.glob("*-audit"))
    page = (folder / "near.html").read_text()
    assert "0 sûr, 1 à vérifier" in page
