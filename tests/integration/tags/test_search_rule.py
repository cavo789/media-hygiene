"""*📌 Make it a rule* on the search page (0396): a period tried, saved, updated.

The tree's burst series of 25 December 2022 (`2022/Durbuy - ours`): a rule of that day
takes it into its folder (the series' own folder is the main one: never below it);
saved into `config.toml`, read back; updated in place from *Update a rule…*.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.rules_file import read_rules
from media_hygiene.services import search_pages as search_service
from tests.integration.tags.test_search_command import _call, fake_server
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response
    from media_hygiene.search.app import SearchApp

_RULE: Final = {
    "name": "Christmas 2022",
    "first": "2022-12-25",
    "last": "2022-12-25",
    "category": "Parties/Christmas",
    "keep_folders": True,
}
_EXISTING: Final = (
    '\n[[classify.rules]]\nname = "Existing folders"\nmatch = "existing_folder"\n'
)


def _serve(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch, calls: list[tuple[str, object]]
) -> list[Response]:
    """Open the search page, send the calls in order, stop it; the answers."""
    answers: list[Response] = []

    async def page(app: SearchApp) -> None:
        for route, body in calls:
            answers.append(await _call(app, route, body))

    monkeypatch.setattr(search_service, "serve_until_ended", fake_server(page))
    result = run(cli, "search")
    assert result.exit_code == 0, result.output
    return answers


def test_a_day_alone_finds_the_files_of_that_day(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Both bounds included, one day alone, a year alone: as the calendars send."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    answers = _serve(
        cli,
        monkeypatch,
        [
            ("POST /api/search", {"day_from": "2022-12-25"}),
            ("POST /api/search", {"day_from": "2022-12-26", "day_to": "2022-12-24"}),
            ("POST /api/search", {"day_from": "2022-12-26"}),
            ("POST /api/search", {"year_from": 2022}),
        ],
    )
    totals = [json.loads(answer.body)["total"] for answer in answers]
    assert totals[0] == totals[1] > 0
    assert totals[2] == 0
    assert totals[3] >= totals[0]


def test_a_rule_tried_shows_where_each_photo_goes(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The series of the day goes to the rule's folder itself; nothing is written."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    answer = _serve(cli, monkeypatch, [("POST /api/period-rule/trial", _RULE)])[0]
    assert answer.status == 200
    tried = json.loads(answer.body)
    assert tried["taken"] > 0
    taken = [hit for hit in tried["hits"] if hit["taken"]]
    assert {hit["to"] for hit in taken} == {"2022\\Parties\\Christmas"}
    assert {hit["name"] for hit in taken} >= {"IMG_0.jpg", "IMG_1.jpg"}
    assert tried["folders"] == [
        {"folder": "2022\\Parties\\Christmas", "files": tried["taken"]}
    ]
    assert not tried["name_taken"]


def test_a_rule_saved_then_updated_in_place(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Written above Existing folders, read back; updated: the same place, new days."""
    config = locations.config_dir / "config.toml"
    text = config.read_text().replace("\n[tags]", _EXISTING + "\n[tags]")
    config.write_text(text, encoding="utf-8")
    updated = {**_RULE, "last": "2022-12-26", "replaces": "Christmas 2022"}
    answers = _serve(
        cli,
        monkeypatch,
        [
            ("POST /api/period-rule", _RULE),
            ("POST /api/period-rule", updated),
            ("GET /api/period-rules", None),
            ("POST /api/period-rule/trial", {**_RULE, "name": "Christmas 2022 "}),
        ],
    )
    assert [answer.status for answer in answers] == [200, 200, 200, 200]
    saved = json.loads(answers[0].body)
    assert saved["dates"] == "2022-12-25..2022-12-25"
    assert saved["modified"]
    assert json.loads(answers[1].body)["dates"] == "2022-12-25..2022-12-26"
    assert [rule.name for rule in read_rules(config)] == [
        "Christmas 2022",
        "Existing folders",
    ]
    listed = json.loads(answers[2].body)["rules"]
    assert [(rule["name"], rule["last"]) for rule in listed] == [
        ("Christmas 2022", "2022-12-26")
    ]
    assert json.loads(answers[3].body)["name_taken"]


def test_a_rule_without_config_is_refused_said(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """No list of rules to write into: 409 and why; a bad rule: 400."""
    answers = _serve(
        cli,
        monkeypatch,
        [
            ("POST /api/period-rule", _RULE),
            ("POST /api/period-rule", {**_RULE, "name": " "}),
        ],
    )
    assert [answer.status for answer in answers] == [409, 400]
    assert json.loads(answers[0].body)["error"]
    assert "Christmas" not in (locations.config_dir / "config.toml").read_text()
