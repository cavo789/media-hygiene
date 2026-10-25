"""`media-hygiene places`: the map of the photos' positions, places saved at once."""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Any

import pytest
from typer.testing import CliRunner

from media_hygiene.places.config_file import read_places
from media_hygiene.services import places as places_service
from tests.support.cli import run
from tests.support.places_map import (
    GARDEN,
    PORT,
    audited_garden,
    call,
    fake_server,
)

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.review.http import Response


@pytest.fixture(name="garden")
def garden_fixture(locations: Locations, monkeypatch: pytest.MonkeyPatch) -> CliRunner:
    """Three photos taken in the garden, audited: the index knows where."""
    return audited_garden(locations, monkeypatch)


def test_the_map_shows_the_clusters_and_saves_a_place(
    garden: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One cluster of three photos; named, it is saved and shown in its place."""
    seen: dict[str, Response] = {}

    async def name_it(app: PlacesApp) -> None:
        seen["state"] = await call(app, "GET /api/state")
        place = {"key": None, "name": "Garden", "latitude": GARDEN[0]}
        place |= {"longitude": GARDEN[1], "radius_m": 100, "home": True}
        seen["saved"] = await call(app, "POST /api/places", {"places": [place]})
        seen["page"] = app.page
        seen["leaflet"] = await call(app, "GET /leaflet.js")

    monkeypatch.setattr(places_service, "run_server", fake_server(name_it))
    result = run(garden, "places")
    assert result.exit_code == 0, result.output
    assert f"open http://127.0.0.1:{PORT}/ in your browser" in result.output
    assert "'place' rule" in result.output
    state = json.loads(seen["state"].body)
    assert [cluster[2:] for cluster in state["clusters"]] == [[3, 0, "", -1]]
    saved = json.loads(seen["saved"].body)
    assert saved["clusters"][0][4] == "Garden"
    assert saved["places"][0]["key"] == 0
    assert [place.name for place in read_places(locations.config_file)] == ["Garden"]
    page = seen["page"]
    assert "tile.openstreetmap.org" in page.policy
    assert page.referrer == "strict-origin"
    assert b"leaflet.js" in page.body
    assert seen["leaflet"].body.startswith(b"/* @preserve")
    assert seen["leaflet"].cacheable
    # 0339: framed on every point but 0, 0, the folders placed too, beside the drawer.
    body = page.body.decode()
    assert "folders.filter((folder) => folder.saved)" in body
    assert ".filter((point) => !unknownSpot(point))" in body
    assert "paddingBottomRight: [hidden(), 0] });\n  }" in body
    assert "loadFolders().then(frame)" in body
    assert "Show every place of the photos" in body


def test_the_town_search_is_offline(
    garden: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Accents and case do not matter; the largest town first."""
    found: list[object] = []

    async def search(app: PlacesApp) -> None:
        answer = await call(app, "POST /api/search", {"text": "liege"})
        found.append(json.loads(answer.body))

    monkeypatch.setattr(places_service, "run_server", fake_server(search))
    assert run(garden, "places").exit_code == 0
    assert len(found) == 1
    assert found[0][0]["name"] == "Liège"  # type: ignore[index]


def test_without_an_index_the_map_is_empty_but_works(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Said at once; places can still be named on the map."""
    monkeypatch.setenv("MEDIA_HYGIENE_CONFIG_DIR", str(locations.config_dir))

    async def nothing(_app: PlacesApp) -> None:
        """Open the map, close it."""

    monkeypatch.setattr(places_service, "run_server", fake_server(nothing))
    result = run(CliRunner(), "places")
    assert result.exit_code == 0, result.output
    assert "No photo with a GPS position in the index" in result.output


def test_a_place_named_like_a_town_nearby_says_so_and_still_saves(
    garden: CliRunner, locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TODO 0239: a hint for a town nearby, none for a nickname or a far namesake."""
    hints: list[str] = []
    seen: dict[str, Any] = {}
    beach = {"latitude": 51.3135, "longitude": 3.1325}

    async def ask(app: PlacesApp) -> None:
        for name, where in (
            ("Blankenberge", beach),
            ("blankenberge ", {"latitude": 51.35, "longitude": 3.2}),  # 5 km, folded
            ("Geer chez papy", beach),
            ("Blankenberge", {"latitude": -33.9, "longitude": 151.2}),
        ):
            answer = await call(app, "POST /api/hint", {"name": name, **where})
            hints.append(json.loads(answer.body)["town"])
        place = {"key": None, "name": "Blankenberge", "radius_m": 100, "home": False}
        saved = await call(app, "POST /api/places", {"places": [place | beach]})
        seen["state"] = json.loads(saved.body)
        seen["bad"] = (await call(app, "POST /api/hint", {"name": "x"})).status

    monkeypatch.setattr(places_service, "run_server", fake_server(ask))
    assert run(garden, "places").exit_code == 0
    assert hints == ["Blankenberge", "Blankenberge", "", ""]
    assert seen["state"]["places"][0]["town"] == "Blankenberge"
    assert [place.name for place in read_places(locations.config_file)] == [
        "Blankenberge"
    ]
    assert seen["bad"] == 400
