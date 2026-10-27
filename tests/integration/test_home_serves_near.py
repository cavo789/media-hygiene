"""0357: the home server serves `review --near` itself, under `/review/near/`."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import WATCH, served_here
from media_hygiene.services import home
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.cli import run
from tests.support.places_map import JSON

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


def test_the_near_review_is_served_under_its_prefix(
    cli: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page, its state, a preview and a decision, all through the home server."""
    assert served_here(("review", "--near")) == "/review/near/"
    choice = {"choices": [{"group": 0, "action": "swap"}]}
    answers = _serve(
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
    answer = _serve(cli, monkeypatch, [("GET /review/near/api/state", None)])[0]
    assert answer.status == 404
