"""`media-hygiene places`: what it refuses, and the errors it explains."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING

import pytest

from media_hygiene.places.board import PlacesBoard
from media_hygiene.review.http import Request, Response
from media_hygiene.services import places as places_service
from tests.support.cli import run
from tests.support.places_map import (
    JSON,
    audited_garden,
    call,
    fake_server,
)

if TYPE_CHECKING:
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp


@pytest.fixture(name="garden")
def garden_fixture(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """Three photos taken in the garden, audited: the index knows where."""
    return audited_garden(locations, monkeypatch)


def test_the_page_refuses_what_it_should(
    garden: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Another host, another origin, no JSON, a bad name, an unknown path."""
    answers: list[int] = []

    async def misbehave(app: PlacesApp) -> None:
        rebind = Request("GET", "/", {"host": "evil.example:4243"})
        other = Request("POST", "/api/places", JSON | {"origin": "http://evil.example"})
        plain = Request("POST", "/api/search", {"host": "127.0.0.1"}, b"{}")
        answers.extend([(await app.handle(r)).status for r in (rebind, other, plain)])
        bad = {"key": None, "name": "A?", "latitude": 1, "longitude": 1}
        for route, body in (
            ("POST /api/places", {"places": [bad]}),
            ("POST /api/places", {"wrong": 1}),
            ("POST /api/search", {"text": 3}),
            ("GET /favicon.ico", None),
            ("DELETE /api/places", None),
        ):
            answers.append((await call(app, route, body)).status)

    monkeypatch.setattr(places_service, "run_server", fake_server(misbehave))
    assert run(garden, "places").exit_code == 0
    assert answers == [403, 403, 415, 422, 422, 400, 404, 405]


def test_the_map_needs_a_config_mount(
    garden: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nowhere to save: refused, with a tip."""
    monkeypatch.delenv("MEDIA_HYGIENE_CONFIG_DIR")
    result = run(garden, "places")
    assert result.exit_code == 1
    assert "mount /config" in result.output


def test_invalid_places_in_the_file_are_named(
    garden: CliRunner, locations: Locations
) -> None:
    """Two homes written by hand: refused at load time, without a trace."""
    locations.config_file.write_text(
        "[classify]\n"
        '[[classify.places]]\nname = "A"\nlatitude = 1\nlongitude = 1\nhome = true\n'
        '[[classify.places]]\nname = "B"\nlatitude = 2\nlongitude = 2\nhome = true\n',
        "utf-8",
    )
    result = run(garden, "places")
    assert result.exit_code != 0
    assert "Invalid configuration (classify.places" in result.output
    assert "Traceback" not in result.output


def test_places_changed_by_hand_after_start_are_named(
    garden: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The file is read again when the map opens: a broken place is a clear error."""
    original = PlacesBoard

    def broken_meanwhile(*args: object) -> object:
        locations.config_file.write_text(
            '[classify]\n[[classify.places]]\nname = "A"\nlatitude = 99\n', "utf-8"
        )
        return original(*args)  # type: ignore[arg-type]

    monkeypatch.setattr(places_service, "PlacesBoard", broken_meanwhile)
    result = run(garden, "places")
    assert result.exit_code == 1
    assert "The places of" in result.output
    assert "are invalid" in result.output


def test_a_duplicate_name_or_a_read_only_file_is_said_on_the_page(
    garden: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page shows why nothing was saved; the page itself is served."""
    answers: list[Response] = []
    shed = {"key": None, "name": "Shed", "latitude": 1, "longitude": 1}

    async def save_twice(app: PlacesApp) -> None:
        answers.append(await call(app, "GET /"))
        answers.append(await call(app, "POST /api/places", {"places": [shed, shed]}))
        locations.config_dir.chmod(0o500)
        try:
            answers.append(await call(app, "POST /api/places", {"places": [shed]}))
        finally:
            locations.config_dir.chmod(0o700)

    monkeypatch.setattr(places_service, "run_server", fake_server(save_twice))
    assert run(garden, "places").exit_code == 0
    assert len(answers) == 3
    page, twice, read_only = answers[0], answers[1], answers[2]
    assert b"leaflet.js" in page.body
    assert twice.status == 422
    assert "two places are named" in json.loads(twice.body)["error"]
    assert read_only.status == 500
    assert "Cannot save config.toml" in json.loads(read_only.body)["error"]


def test_a_damaged_index_is_a_clear_error(
    garden: CliRunner, locations: Locations
) -> None:
    """Not an index: said, with what to do."""
    locations.index_file.write_bytes(b"not a database, not at all" * 100)
    result = run(garden, "places")
    assert result.exit_code == 1
    assert "cannot be read" in result.output
