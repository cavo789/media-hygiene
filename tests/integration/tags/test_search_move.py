"""*Move to an event…* on the search page (0403): seen by source folder, then moved."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from tests.support.cli import run
from tests.support.search_page import serve_search

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

_DAY: Final = {"text": "", "day_from": "2022-12-25", "day_to": "2022-12-25"}


def test_the_photos_picked_are_shown_then_moved_without_a_rule(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Before classify: refused, said; after: a view, a name refused, then the move."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    found = serve_search(cli, monkeypatch, [("POST /api/search", _DAY)])[0]
    keys = [hit["key"] for hit in json.loads(found.body)["hits"]]
    assert keys
    early = serve_search(cli, monkeypatch, [("POST /api/move/view", {"keys": keys})])[0]
    assert early.status == 409
    assert "classify" in json.loads(early.body)["error"]
    assert run(cli, "classify").exit_code == 0
    config = locations.config_file.read_text(encoding="utf-8")
    answers = serve_search(
        cli,
        monkeypatch,
        [
            ("POST /api/move/view", {"keys": keys, "name": "Noël"}),
            ("POST /api/move", {"keys": keys, "name": "Fêtes/Noël"}),
            ("POST /api/move", {"keys": keys, "name": "Noël"}),
        ],
    )
    assert [answer.status for answer in answers] == [200, 409, 200]
    view = json.loads(answers[0].body)
    assert view["target"].endswith("2022\\2022-12\\Noël")
    assert sum(source["files"] for source in view["sources"]) == len(keys)
    assert "one name" in json.loads(answers[1].body)["error"]
    done = json.loads(answers[2].body)
    assert done["moved"] + done["already"] + done["fixed"] + done["unknown"] == len(
        keys
    )
    moved = list(locations.data_dir.rglob("2022/2022-12/Noël/*"))
    assert len(moved) >= done["moved"] > 0
    assert locations.config_file.read_text(encoding="utf-8") == config  # no rule
