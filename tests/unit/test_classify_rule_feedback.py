"""What the user sees of the rules: files per rule, the rules that decided nothing."""

from __future__ import annotations

from io import StringIO
from pathlib import Path

from rich.console import Console

from media_hygiene.classify.engine import Scope, classify
from media_hygiene.classify.models import MediaInput
from media_hygiene.classify.plan_build import build_plan
from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.workbook.rows import file_rows
from media_hygiene.classify.workbook.sheets import Labels
from media_hygiene.classify.workbook.summary import summary_rows
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.console.classify_view import show_classification
from media_hygiene.console.output import Output
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.scan.models import VisualFacts
from media_hygiene.services.classify import ClassifyResult

ROOT = Path("/data/c/Photos")
SETTINGS = ClassifySettings(
    rules=(
        ClassifyRule(
            name="Drone [DJI]", match=RuleMatch.CAMERA, pattern="DJI", category="Drone"
        ),
        ClassifyRule(
            name="Italy",
            match=RuleMatch.DATE_RANGE,
            dates="2023-07-01..2023-07-15",
            category="Italy",
        ),
    )
)


def classified() -> ClassifyResult:
    """A drone shot and an ordinary one; no trip to Italy."""
    files = [
        MediaInput(
            ROOT / name,
            ROOT,
            10,
            0,
            VisualFacts(0, 0, 4000, 3000, 0.0, "2019:06:02 10:00:00", camera),
        )
        for name, camera in (("a.jpg", "DJI FC3170"), ("b.jpg", "Pixel"))
    ]
    return ClassifyResult(classify(files, SETTINGS, Scope()), 0)


def test_the_console_counts_files_per_rule_and_names_unused_rules() -> None:
    """`Drone [DJI]` decided one file; `Italy` decided none: a warning."""
    buffer = StringIO()
    show_classification(Output(Console(file=buffer, width=100)), classified())
    text = buffer.getvalue()
    assert "Drone [DJI]" in text
    assert "no-signal" in text
    assert "Rules that decided nothing: Italy." in text


def test_the_plan_and_the_workbook_carry_the_rule() -> None:
    """The reason column shows the rule's name; the summary lists unused rules."""
    plan = build_plan(
        classified().classification, SETTINGS, HostPathMapper(Path("/data"))
    )
    assert plan.unused_rules == ("Italy",)
    drone = next(row for row in plan.rows if row.rule)
    assert drone.why == "Drone [DJI]"
    reasons = {row[8] for row in file_rows(plan, Labels.current())}
    assert reasons == {"Drone [DJI] (90)", "no-signal (0)"}
    summary = summary_rows(plan)
    assert ("Drone [DJI]", 1) in summary
    assert ("Italy", 0) in summary
