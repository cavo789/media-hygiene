"""Serve `home` as the `mh` that keeps it up does, and send it requests (0356, 0357)."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Request
from media_hygiene.review.step_watch import WATCH
from media_hygiene.services import home
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.cli import run
from tests.support.places_map import JSON

if TYPE_CHECKING:
    from collections.abc import Callable

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.review.ending import EndingDoor
    from media_hygiene.review.http import Response

LOCAL: Final = {"host": "127.0.0.1"}


def serve_home(
    cli: CliRunner,
    monkeypatch: pytest.MonkeyPatch,
    calls: list[tuple[str, object]],
) -> list[Response]:
    """Start `home`, send the calls (`"GET /path"`, JSON body or None), then Ctrl+C."""
    answers: list[Response] = []

    async def serve(door: EndingDoor, _port: int, ready: Callable[[int], None]) -> int:
        ready(8088)
        for route, body in calls:
            method, path = route.split()
            data = json.dumps(body).encode() if body is not None else b""
            request = Request(method, path, JSON if body is not None else LOCAL, data)
            answers.append(await door.handle(request))
        raise KeyboardInterrupt

    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, WATCH.kept)
    monkeypatch.setattr(home, "serve_until_ended", serve)
    result = run(cli, "home")
    assert result.exit_code == 0, result.output
    return answers
