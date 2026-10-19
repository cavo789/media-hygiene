"""Report -> decisions.json -> `clean --decisions`: undoable, refused when stale."""

from __future__ import annotations

import html
import json
import re
from typing import TYPE_CHECKING

import pytest

from media_hygiene.errors import DecisionsError
from media_hygiene.plan.review import PairAction
from media_hygiene.report.decisions import DecisionsFile, PairDecision
from media_hygiene.scan.progress import NullProgress
from media_hygiene.services.audit import AuditService
from media_hygiene.services.review import review_choices
from tests.support.cli import run
from tests.support.media import MediaFactory
from tests.support.pairs import IPHONE, SUMMER, clean_swapped_and_skipped
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

SELECT = re.compile(
    r'<select class="decision" data-kept-in="([^"]*)" data-removed-from="([^"]*)"'
)
ROOTS = re.compile(r"const roots = (.*);")


def decide(report: Path, choices: dict[tuple[str, str], str]) -> str:
    """Do what the report's page does: list its pairs, keep the decided ones."""
    page = report.read_text(encoding="utf-8")
    pairs = [(html.unescape(k), html.unescape(r)) for k, r in SELECT.findall(page)]
    roots_match = ROOTS.search(page)
    assert roots_match is not None
    decided = [
        {"kept_in": kept, "removed_from": removed, "action": choices[kept, removed]}
        for kept, removed in pairs
        if (kept, removed) in choices
    ]
    assert len(decided) == len(choices)
    roots = json.loads(roots_match[1])
    return json.dumps({"version": 1, "roots": roots, "pairs": decided})


def test_report_decisions_drive_the_clean(cli: CliRunner, locations: Locations) -> None:
    """Swap keeps the backup's HEIC, skip keeps the backup's summer copy; undo too."""
    data = locations.data_dir
    assert run(cli, "audit").exit_code == 0
    [report] = locations.reports_dir.glob("*-audit/report.html")
    choices = {IPHONE: PairAction.SWAP.value, SUMMER: PairAction.SKIP.value}
    (locations.reports_dir / "decisions.json").write_text(decide(report, choices))
    clean_swapped_and_skipped(cli, data)


def test_missing_file_fails_before_the_audit(cli: CliRunner) -> None:
    """A wrong path is reported at once, not after a long audit."""
    result = run(cli, "clean", "--yes", "--decisions", "nowhere.json")
    assert result.exit_code == 1
    assert "Cannot read the decisions file" in result.output
    assert "Audit summary" not in result.output


def review(
    roots: tuple[str, ...], *pairs: tuple[str, str, PairAction]
) -> DecisionsFile:
    """A decisions file with these roots and pair decisions."""
    decided = tuple(
        PairDecision(kept_in=k, removed_from=r, action=a) for k, r, a in pairs
    )
    return DecisionsFile(version=1, roots=roots, pairs=decided)


@pytest.mark.parametrize(
    ("decisions", "error"),
    [
        (review(("E:\\",), (*IPHONE, PairAction.SKIP)), "made on other folders"),
        (review(("C:\\",), ("C:\\Gone", "C:\\Away", PairAction.SKIP)), "no longer"),
        (review(("C:\\",), ("C:\\X", "C:\\X", PairAction.SWAP)), "inside one folder"),
        (review(("C:\\",), ("C:\\Y", "C:\\Z", PairAction.SWAP)), "is protected"),
        (review(("C:\\",), ("C:\\Y", "C:\\Z", PairAction.LINK)), "both names cannot"),
    ],
)
def test_foreign_stale_or_impossible_decisions_are_refused(
    locations: Locations, decisions: DecisionsFile, error: str
) -> None:
    """Other folders, a vanished pair, an impossible swap: the file is refused."""
    media = MediaFactory(locations.data_dir)
    photo = media.image("c/X/a.jpg", seed=1)
    media.copy(photo, "c/X/a (1).jpg")
    other = media.image("c/Y/b.jpg", seed=2)
    media.copy(other, "c/Z/deeper/b.jpg")
    media.copy(other, "c/Z/b.jpg")
    runtime = make_runtime(locations, {"folders": {"protected": ["C:\\Y"]}})
    findings = AuditService(runtime, NullProgress()).run()
    with pytest.raises(DecisionsError, match=error):
        review_choices(runtime, findings, decisions)
