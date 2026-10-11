"""`classify` with a `person` rule: the photos of someone named go to its category."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.plan_file import ClassifyPlan
from tests.support.cli import run
from tests.support.faces import coloured

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

# One face of person 0 confirmed: her other photos come close enough to it.
NAMED = """
[people]
[[people.person]]
name = "Chloé"
faces = ["{data}/c/Holidays/IMG_0.png#0"]
"""
RULE = """
[[classify.rules]]
name = "With Chloé"
match = "person"
names = [{names}]
category = "People/Chloé"
"""


def named(locations: Locations) -> str:
    """`[people]` naming Chloé, by a face of the test mount."""
    return NAMED.format(data=locations.data_dir)


def test_classify_files_the_events_of_a_named_person(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """She is on one photo of a dated party of six: the whole party takes the rule."""
    party = locations.data_dir / "c" / "Party"
    for minute in range(6):
        name = f"IMG_20230501_10{minute:02d}00.png"
        coloured(party / name, 0 if minute == 2 else -1, (96 + minute, 64))
    assert run(cli, "audit").exit_code == 0
    assert run(cli, "people").exit_code == 0
    assert apps
    config = locations.config_file
    config.write_text(RULE.format(names='"chloe"') + named(locations), "utf-8")
    result = run(cli, "classify")
    assert result.exit_code == 0, result.output
    (folder,) = locations.reports_dir.glob("*-classify")
    plan = ClassifyPlan.model_validate_json((folder / "plan.json").read_text("utf-8"))
    hers = {row.name for row in plan.rows if row.rule == "With Chloé"}
    assert hers == {path.name for path in party.iterdir()}
    assert {row.category for row in plan.rows if row.name in hers} == {"People/Chloé"}


def test_a_rule_naming_nobody_stops_classify(
    cli: CliRunner, locations: Locations
) -> None:
    """Manon is nobody yet: the run stops before reading anything, naming the rule."""
    locations.config_file.write_text(
        RULE.format(names='"Manon"') + named(locations), "utf-8"
    )
    result = run(cli, "classify")
    assert result.exit_code != 0
    text = " ".join(result.output.split())
    assert "Rule 'With Chloé': nobody is named \"Manon\"" in text
    assert "Named: Chloé." in text
