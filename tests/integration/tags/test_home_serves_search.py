"""0356: the home server serves `search` and `browse` itself: a click is a link."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.cli.home_state import home_state
from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import WATCH
from media_hygiene.services import home
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.cli import run
from tests.support.places_map import JSON
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.ending import EndingDoor
    from media_hygiene.review.http import Response

_LOCAL = {"host": "127.0.0.1"}


def _serve(
    cli: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, object]],
) -> list[Response]:
    """Start `home` as the `mh` that keeps it up does, send the calls, then Ctrl+C."""
    answers: list[Response] = []

    async def serve(door: EndingDoor, _port: int, ready: Callable[[int], None]) -> int:
        ready(8088)
        for route, body in calls:
            method, path = route.split()
            data = json.dumps(body).encode() if body is not None else b""
            request = Request(method, path, JSON if body is not None else _LOCAL, data)
            answers.append(await door.handle(request))
        raise KeyboardInterrupt

    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    monkeypatch.setattr(home, "serve_until_ended", serve)
    result = run(cli, "home")
    assert result.exit_code == 0, result.output
    return answers


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
    answers = _serve(
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
    answers = _serve(
        cli, monkeypatch, [("GET /api/state", None), ("GET /api/step", None)]
    )
    state, step = answers[0], answers[1]
    assert "actions" in json.loads(state.body)
    assert json.loads(step.body)["state"] == "idle"
