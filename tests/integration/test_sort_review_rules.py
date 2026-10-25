"""0393: Your rules: what each rule decided, dead ones removed, one turned to dates."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.classify.rules.kinds import RuleMatch
from media_hygiene.classify.rules_file import add_rule, read_rules
from media_hygiene.config.classify_rules import ClassifyRule
from media_hygiene.config.loader import write_default_config
from media_hygiene.constants import Locale
from tests.support.sort_review import call, classified, reopened

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

PARTY_RULE = ClassifyRule(
    name="Kermesse",
    match=RuleMatch.PATH,
    pattern="(?i)juillet 2016",
    category="Kermesse",
)
DEAD_RULES = tuple(
    ClassifyRule(name=name, match=RuleMatch.PATH, pattern=pattern, category="X")
    for name, pattern in (("Sun Park", "(?i)sun ?park"), ("Le Lucana", "(?i)lucana"))
)


def with_rules(locations: Locations) -> None:
    """The default config.toml, a folder-name rule of the party and two dead ones."""
    write_default_config(locations.config_file, Locale.EN)
    for rule in (PARTY_RULE, *DEAD_RULES):
        add_rule(locations.config_file, rule)


def lines(answer: Response) -> dict[str, dict[str, object]]:
    """The rules of the view, by name."""
    return {line["name"]: line for line in json.loads(answer.body)["rules"]}


def test_the_view_counts_what_each_rule_decided(locations: Locations) -> None:
    """The party's rule: its six files and its event's day; the dead ones: none."""
    with_rules(locations)
    runtime, _workbook = classified(locations)
    app = reopened(runtime)
    found = lines(asyncio.run(call(app, "GET /api/rules")))
    party = found["Kermesse"]
    assert (party["files"], party["first"], party["last"]) == (
        6,
        "2016-07-14",
        "2016-07-14",
    )
    assert found["Sun Park"]["files"] == found["Le Lucana"]["files"] == 0
    assert found["Existing folders"]["built_in"]


def test_the_view_is_shown_by_kind_the_file_keeps_its_order(
    locations: Locations,
) -> None:
    """0395: the dialog's order is its own; config.toml is not touched by opening it."""
    with_rules(locations)
    runtime, _workbook = classified(locations)
    before = locations.config_file.read_bytes()
    answer = asyncio.run(call(reopened(runtime), "GET /api/rules"))
    shown = json.loads(answer.body)["rules"]
    assert locations.config_file.read_bytes() == before
    names = [rule.name for rule in read_rules(locations.config_file)]
    assert sorted(line["position"] for line in shown) == list(range(len(names)))
    assert [names[line["position"]] for line in shown] == [
        line["name"] for line in shown
    ]
    paths = [line["name"] for line in shown if line["match"] == "path"]
    assert paths[0] == "Kermesse"  # it decided files; the two dead ones after it
    assert shown[-1]["built_in"]
    assert all(line["group"] for line in shown)


def test_dead_rules_are_removed_their_neighbours_comments_kept(
    locations: Locations,
) -> None:
    """Both dead rules removed in one write; the other rules and comments stay."""
    with_rules(locations)
    runtime, _workbook = classified(locations)
    app = reopened(runtime)
    comments = locations.config_file.read_text("utf-8").count("\n#")
    body = {"names": ["Sun Park", "Le Lucana"]}
    answer = asyncio.run(call(app, "POST /api/rules/remove", body))
    assert answer.status is HTTPStatus.OK
    names = [rule.name for rule in read_rules(locations.config_file)]
    assert "Sun Park" not in names
    assert "Le Lucana" not in names
    assert "Kermesse" in names
    assert set(lines(answer)) == set(names)
    assert locations.config_file.read_text("utf-8").count("\n#") == comments
    again = asyncio.run(call(app, "POST /api/rules/remove", {"names": ["Sun Park"]}))
    assert again.status is HTTPStatus.UNPROCESSABLE_ENTITY


def test_a_folder_name_rule_is_turned_into_dates_in_its_place(
    locations: Locations,
) -> None:
    """Same place in the list; nothing it decided lost; no event chosen."""
    with_rules(locations)
    runtime, _workbook = classified(locations)
    app = reopened(runtime)
    party = lines(asyncio.run(call(app, "GET /api/rules")))["Kermesse"]
    place = [rule.name for rule in read_rules(locations.config_file)].index("Kermesse")
    body = {
        "event": party["event"],
        "name": "Kermesse",
        "first": party["first"],
        "last": party["last"],
        "category": party["category"],
        "replaces": "Kermesse",
    }

    async def convert() -> tuple[Response, Response]:
        preview = await call(app, "POST /api/rule/preview", body)
        return preview, await call(app, "POST /api/rule", body)

    preview, saved = asyncio.run(convert())
    assert json.loads(preview.body)["lost"] == 0
    assert not json.loads(preview.body)["taken"]
    assert saved.status is HTTPStatus.OK
    assert json.loads(saved.body)["view"]["card"]["page"] is None
    rules = read_rules(locations.config_file)
    assert rules[place].name == "Kermesse"
    assert rules[place].match is RuleMatch.DATE_RANGE
    assert rules[place].dates == "2016-07-14..2016-07-14"
    assert rules[place].keep_folders
