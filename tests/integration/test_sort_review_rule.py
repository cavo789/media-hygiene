"""0392: *Remember as a rule* writes the event shown as a `date_range` rule."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.classify.plan_file import ClassifyPlan
from media_hygiene.classify.rules_file import read_rules
from media_hygiene.config.loader import write_default_config
from media_hygiene.constants import Locale
from tests.support.runtime import make_runtime
from tests.support.sort_review import call, classified, first_event, reopened
from tests.support.sorting import PARTY_SHOTS, classify

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

FOLDER = "Fêtes/Kermesse"


def rule_of(event: str, name: str = "Kermesse") -> dict[str, object]:
    """The dialog's fields for the library's party, 14 July 2016."""
    return {
        "event": event,
        "name": name,
        "first": "2016-07-14",
        "last": "2016-07-14",
        "category": FOLDER,
    }


def test_the_preview_counts_what_the_rule_would_take(locations: Locations) -> None:
    """The party's six shots, nothing else on that day; nothing written."""
    write_default_config(locations.config_file, Locale.EN)
    before = locations.config_file.read_text("utf-8")
    runtime, _workbook = classified(locations)
    app = reopened(runtime)

    async def ask() -> Response:
        event, _rows = await first_event(app)
        return await call(app, "POST /api/rule/preview", rule_of(event))

    answer = json.loads(asyncio.run(ask()).body)
    assert (answer["files"], answer["this_event"], answer["others"]) == (
        PARTY_SHOTS,
        PARTY_SHOTS,
        0,
    )
    assert not answer["taken"]
    assert locations.config_file.read_text("utf-8") == before


def test_a_rule_saved_is_read_back_and_applied_by_the_next_classify(
    locations: Locations,
) -> None:
    """Above Existing folders, comments kept; the event chosen; classify applies it."""
    write_default_config(locations.config_file, Locale.EN)
    comments = locations.config_file.read_text("utf-8").count("\n#")
    runtime, _workbook = classified(locations)
    app = reopened(runtime)

    async def save() -> tuple[Response, Response]:
        event, _rows = await first_event(app)
        first = await call(app, "POST /api/rule", rule_of(event))
        again = await call(app, "POST /api/rule", rule_of(event, "kermesse"))
        return first, again

    saved, again = asyncio.run(save())
    assert saved.status is HTTPStatus.OK
    answer = json.loads(saved.body)
    assert (answer["name"], answer["dates"]) == ("Kermesse", "2016-07-14..2016-07-14")
    assert answer["view"]["card"]["page"]["category"] == FOLDER
    assert again.status is HTTPStatus.UNPROCESSABLE_ENTITY
    assert "already named" in json.loads(again.body)["error"]
    text = locations.config_file.read_text("utf-8")
    assert text.count("\n#") == comments
    names = [rule.name for rule in read_rules(locations.config_file)]
    assert names.index("Kermesse") == names.index("Existing folders") - 1
    rule = next(r for r in read_rules(locations.config_file) if r.name == "Kermesse")
    assert rule.keep_folders
    workbook = classify(make_runtime(locations))  # config.toml read again
    plan = ClassifyPlan.model_validate_json(
        workbook.with_name("plan.json").read_text("utf-8")
    )
    party = [row for row in plan.rows if row.date and row.date.startswith("2016-07-14")]
    assert {row.rule for row in party} == {"Kermesse"}
    assert {row.folder for row in party} == {f"2016/{FOLDER}"}
