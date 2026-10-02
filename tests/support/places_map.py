"""The map of `places` without a browser: a server that only says it is ready.

Three photos taken in a fictitious garden, audited, so that the index knows where.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from typer.testing import CliRunner

from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.http import Request
from tests.support.cli import run
from tests.support.scenes import Shot, write_shot

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    import pytest

    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.review.http import Response

PORT: Final = 4243
GARDEN: Final = (50.30012, 5.10021)  # a fictitious place
JSON: Final = {"host": "127.0.0.1:4243", "content-type": "application/json"}


async def call(app: PlacesApp, route: str, body: object = None) -> Response:
    """Send one request to the app, as the page does; `route`: `GET /api/state`."""
    method, path = route.split()
    headers = JSON if body is not None else {"host": "127.0.0.1"}
    data = json.dumps(body).encode() if body is not None else b""
    return await app.handle(Request(method, path, headers, data))


def fake_server(action: Callable[[PlacesApp], Awaitable[None]]) -> object:
    """A server that says it is ready, lets `action` act, then gets Ctrl+C."""

    async def serve(app: PlacesApp, _port: int, ready: Callable[[int], None]) -> None:
        ready(PORT)
        await action(app)
        raise KeyboardInterrupt

    return serve


def audited_garden(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """Mount everything, write three located photos, audit them."""
    for kind in MountKind:
        monkeypatch.setenv(
            f"MEDIA_HYGIENE_{kind.value.upper()}_DIR", str(locations.path_of(kind))
        )
    for index in range(3):
        shot = Shot(60 + index, taken_at=f"2023:07:01 1{index}:00:00")
        write_shot(locations.data_dir / f"c/Photos/IMG_{index}.jpg", shot, GARDEN)
    runner = CliRunner()
    assert run(runner, "audit").exit_code == 0
    return runner
