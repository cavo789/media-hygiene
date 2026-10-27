"""0357: the home server serves `review --near` itself, under `/review/near/`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.review.step_watch import served_here
from tests.support.home_serving import serve_home

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations


def test_the_near_review_is_served_under_its_prefix(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page, its state, a preview and a decision, all through the home server."""
    assert served_here(("review", "--near")) == "/review/near/"
    choice = {"choices": [{"group": 0, "action": "swap"}]}
    answers = serve_home(
        cli,
        monkeypatch,
        [
            ("GET /review/near", None),
            ("GET /review/near/", None),
            ("GET /review/near/api/state", None),
            ("POST /review/near/api/near", choice),
            ("GET /review/near/api/file", None),
            ("GET /api/state", None),
        ],
    )
    redirect, page, state, decided, held, home_state = (*answers,)  # pylint: disable=unbalanced-tuple-unpacking
    assert redirect.status == 303
    assert "Location: /review/near/" in redirect.headers
    assert page.status == 200
    assert '"api/state"' in page.body.decode()  # relative: answered under the prefix
    groups = json.loads(state.body)["groups"]
    assert groups
    preview = groups[0]["kept"]["preview"]
    assert preview.startswith("preview/")
    assert decided.status == 200
    assert json.loads(held.body)["entries"][0]["action"] == "swap"
    assert (locations.reports_dir / "decisions.json").exists()
    assert "actions" in json.loads(home_state.body)  # the home page keeps its paths


def test_before_the_page_nothing_answers(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The review's API waits for its page: no session yet."""
    answer = serve_home(cli, monkeypatch, [("GET /review/near/api/state", None)])[0]
    assert answer.status == 404
