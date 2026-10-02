"""`places` searching OpenStreetMap: a fake Nominatim on the loopback, no network."""

from __future__ import annotations

import json
import socket
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import TYPE_CHECKING, ClassVar, Final, override

import pytest

from media_hygiene.places.config_file import read_places
from media_hygiene.services import places as places_service
from tests.support.cli import run
from tests.support.places_map import audited_garden, call, fake_server

if TYPE_CHECKING:
    from collections.abc import Iterator

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.review.http import Response

RECORDED: Final = Path(__file__).resolve().parents[1] / "fixtures" / "nominatim"
URL_VARIABLE: Final = "MEDIA_HYGIENE_PLACES__NOMINATIM_URL"
LOOPBACK: Final = "127.0.0.1"


class _Nominatim(BaseHTTPRequestHandler):
    """Answers every search with the recorded answer; remembers the requests."""

    seen: ClassVar[list[tuple[str, str]]] = []

    def do_GET(self) -> None:  # pylint: disable=invalid-name
        """Record the path and the User-Agent, answer the recorded results."""
        self.seen.append((self.path, self.headers.get("User-Agent", "")))
        body = (RECORDED / "search.json").read_bytes()
        self.send_response(200)
        self.send_header("Content-Type", "application/json")
        self.send_header("Content-Length", str(len(body)))
        self.end_headers()
        self.wfile.write(body)

    @override
    def log_message(self, *_args: object) -> None:
        """Quiet."""


@pytest.fixture(name="nominatim")
def nominatim_fixture(monkeypatch: pytest.MonkeyPatch) -> Iterator[None]:
    """A fake Nominatim on the loopback, the one `[places] nominatim_url` names."""
    _Nominatim.seen.clear()
    server = ThreadingHTTPServer((LOOPBACK, 0), _Nominatim)
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()
    monkeypatch.setenv(URL_VARIABLE, f"http://{LOOPBACK}:{server.server_address[1]}")
    yield
    server.shutdown()
    server.server_close()


@pytest.fixture(name="garden")
def garden_fixture(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """Three photos taken in the garden, inside the fictitious village's outline."""
    return audited_garden(locations, monkeypatch)


def _open_map(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner
) -> dict[str, Response]:
    """Search OpenStreetMap, save the first area; every answer by name."""
    seen: dict[str, Response] = {}

    async def act(app: PlacesApp) -> None:
        seen["page"] = app.page
        seen["found"] = await call(app, "POST /api/osm", {"text": "Fictiville"})
        if seen["found"].status != 200:
            return
        area = json.loads(seen["found"].body)["areas"][0]
        place = {"key": None, "name": area["name"], "latitude": area["latitude"]}
        place |= {"longitude": area["longitude"], "osm": area["osm"]}
        place |= {"area": area["area"], "radius_m": 200, "home": False}
        seen["saved"] = await call(app, "POST /api/places", {"places": [place]})

    monkeypatch.setattr(places_service, "run_server", fake_server(act))
    result = run(runner, "places")
    assert result.exit_code == 0, result.output
    return seen


@pytest.mark.usefixtures("nominatim")
def test_an_area_found_online_is_saved_and_names_the_photos(
    garden: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The text alone is sent, under the tool's name; the garden lies in the village."""
    seen = _open_map(monkeypatch, garden)
    assert b'id="osmButton"' in seen["page"].body
    assert b"ODbL" in seen["page"].body
    found = json.loads(seen["found"].body)
    assert [area["osm"] for area in found["areas"]] == ["R9000001", "W9000002"]
    assert len(_Nominatim.seen) == 1
    path, agent = _Nominatim.seen[0]
    assert path.startswith("/search?q=fictiville&")
    assert agent.startswith("media-hygiene/")
    saved = json.loads(seen["saved"].body)
    assert saved["clusters"][0][3] == "Fictiville"
    [village] = read_places(locations.config_file)
    assert (village.osm, len(village.area or ())) == ("R9000001", 1)


def test_without_an_address_there_is_no_online_search(
    garden: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """`nominatim_url = ""`: no button, and the route does not exist."""
    monkeypatch.setenv(URL_VARIABLE, "")
    seen = _open_map(monkeypatch, garden)
    assert b'id="osmButton"' not in seen["page"].body
    assert seen["found"].status == 404


def test_offline_the_page_says_so(
    garden: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Nothing listens: a sentence for the page, the offline search still works."""
    with socket.socket() as probe:
        probe.bind((LOOPBACK, 0))
        closed = probe.getsockname()[1]
    monkeypatch.setenv(URL_VARIABLE, f"http://{LOOPBACK}:{closed}")
    seen = _open_map(monkeypatch, garden)
    assert seen["found"].status == 502
    assert "Cannot reach" in json.loads(seen["found"].body)["error"]
