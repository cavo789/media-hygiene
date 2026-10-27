"""0356: the home server serves `search` and `browse` itself: a click is a link."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.cli.home_state import home_state
from tests.support.cli import run
from tests.support.home_serving import serve_home
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_search_is_a_plain_link_served_here(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The step answers the page's path, nothing ends; the page and its search work."""
    assert run(cli, "tags", "--no-describe").exit_code == 0
    search = home_state(make_runtime(locations)).action("search")
    assert search is not None
    assert search.number is not None
    step = {"number": search.number, "command": search.command}
    asked = {"text": "durbuy"}
    answers = serve_home(
        cli,
        monkeypatch,
        [
            ("GET /", None),
            ("POST /api/step", step),
            ("POST /api/search", asked),
            ("GET /browse", None),
            ("GET /search", None),
        ],
    )
    assert answers[0].status == 200
    assert b"home" in answers[0].body
    assert json.loads(answers[1].body) == {
        "page": "/search",
        "command": search.command,
    }
    assert json.loads(answers[2].body)["total"] == 3
    assert answers[3].status == 200
    shown = answers[4].body.decode()
    assert 'id="homeLink" href="/" data-shared="1"' in shown
    assert not (locations.reports_dir / ".mh-step.json").exists()


def test_the_home_page_keeps_its_own_paths(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Its state and the step's state still answer, never the search's."""
    answers = serve_home(
        cli, monkeypatch, [("GET /api/state", None), ("GET /api/step", None)]
    )
    state, step = answers[0], answers[1]
    assert "actions" in json.loads(state.body)
    assert json.loads(step.body)["state"] == "idle"
