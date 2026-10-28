"""`places`: a cluster set aside (0234), its photos given a place by hand (0237).

The garden's three photos are one cluster. Set aside, it is hidden, then restored.
Given to Geer (one photo left out), the cluster keeps one photo, Geer lists two, by
content; renamed on the map, the entry follows; one taken back; the place deleted,
its photos go with it. A photo moved and renamed since is still Geer's.
"""

from __future__ import annotations

import json
import tomllib
from typing import TYPE_CHECKING, Final, cast

from media_hygiene.config.classify_settings import ClassifySettings
from media_hygiene.places.config_aside import read_aside
from media_hygiene.places.config_photos import read_place_photos
from media_hygiene.scan.hashing import full_digest
from media_hygiene.services import places as places_service
from tests.support.cli import run
from tests.support.places_map import audited_garden, call, fake_server

if TYPE_CHECKING:
    from pathlib import Path

    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.review.http import Response

GEER: Final = {"key": None, "name": "Geer", "latitude": 50.31, "longitude": 5.11}
JPEG_START: Final = b"\xff\xd8"


def _map(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, routes: list[tuple[str, object]]
) -> list[Response]:
    """Open the map, send each route (a callable body sees the answers so far)."""
    seen: list[Response] = []

    async def act(app: PlacesApp) -> None:
        for route, body in routes:
            sent = body(seen) if callable(body) else body
            seen.append(await call(app, route, sent))

    monkeypatch.setattr(places_service, "run_server", fake_server(act))
    result = run(runner, "places")
    assert result.exit_code == 0, result.output
    return seen


def _json(answer: Response) -> dict[str, object]:
    """The answer's body."""
    assert answer.status == 200, answer.body
    found: dict[str, object] = json.loads(answer.body)
    return found


def _comments(config: Path) -> list[str]:
    """The comment lines of the file."""
    return [line for line in config.read_text("utf-8").splitlines() if "#" in line]


def test_a_cluster_set_aside_is_hidden_then_restored(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Read back from the file each time; the file's comments kept."""
    runner = audited_garden(locations, monkeypatch)
    config = locations.config_file
    comments = _comments(config)
    assert comments  # the default file, written by the audit

    def middle(seen: list[Response]) -> dict[str, object]:
        latitude, longitude = _json(seen[0])["clusters"][0][:2]  # type: ignore[index]
        return {"latitude": latitude, "longitude": longitude}

    answers = _map(
        monkeypatch,
        runner,
        [
            ("GET /api/state", None),
            ("POST /api/aside", middle),
            ("POST /api/aside", lambda seen: middle(seen) | {"restore": True}),
        ],
    )
    aside = _json(answers[1])
    assert aside["clusters"][0][5] == 0  # type: ignore[index]
    [circle] = cast("list[dict[str, object]]", aside["aside"])
    assert (circle["pictures"], circle["cluster"], circle["radius_m"]) == (3, 0, 150)
    restored = _json(answers[2])
    rows = cast("list[list[object]]", restored["clusters"])
    assert (restored["aside"], rows[0][5]) == ([], -1)
    assert not read_aside(config)
    assert _comments(config) == comments


def test_photos_given_to_a_place_follow_it_and_come_back(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Give two of three, rename the place, take one back, delete the place."""
    runner = audited_garden(locations, monkeypatch)
    config = locations.config_file

    def give(seen: list[Response]) -> dict[str, object]:
        first = _json(seen[1])["photos"][0]  # type: ignore[index]
        left_out = [[first["folder"], first["name"]]]
        return {"action": "give", "cluster": 0, "place": "geer", "left_out": left_out}

    def take_back(seen: list[Response]) -> dict[str, object]:
        hand = _json(seen[4])["places"][0]["hand"]  # type: ignore[index]
        return {"action": "remove", "sha256": hand[0]["sha256"]}

    renamed = GEER | {"key": 0, "name": "Geer house"}
    answers = _map(
        monkeypatch,
        runner,
        [
            ("POST /api/places", {"places": [GEER]}),
            ("GET /api/cluster/0", None),
            ("POST /api/place-photos", give),
            ("GET /api/cluster/0", None),
            ("POST /api/places", {"places": [renamed]}),
            ("POST /api/place-photos", take_back),
            ("POST /api/place-photos", {"action": "give", "cluster": 0, "place": "X"}),
        ],
    )
    given = _json(answers[2])
    assert given["clusters"][0][2:4] == [1, 0]  # type: ignore[index]
    hand = given["places"][0]["hand"]  # type: ignore[index]
    assert len(hand) == 2
    assert all(photo["now"].startswith("C:\\Photos\\IMG_") for photo in hand)
    assert all(photo["preview"].startswith("preview/") for photo in hand)  # 0417
    photos = read_place_photos(config)[0].photos
    files = sorted((locations.data_dir / "c" / "Photos").glob("IMG_*.jpg"))
    assert {photo.sha256 for photo in photos} < {full_digest(path) for path in files}
    assert len(_json(answers[3])["photos"]) == 1  # type: ignore[arg-type]
    assert len(_json(answers[5])["places"][0]["hand"]) == 1  # type: ignore[index]
    assert answers[6].status == 422
    [entry] = read_place_photos(config)
    assert (entry.place, len(entry.photos)) == ("Geer house", 1)
    deleted = _map(monkeypatch, runner, [("POST /api/places", {"places": []})])
    assert _json(deleted[0])["places"] == []
    assert not read_place_photos(config)
    classify = tomllib.loads(config.read_text("utf-8")).get("classify", {})
    ClassifySettings.model_validate(classify)  # never an entry naming nothing


def test_a_photo_given_then_moved_and_renamed_is_still_the_places(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Matched by content: a folder renamed in Explorer changes nothing."""
    runner = audited_garden(locations, monkeypatch)
    _map(
        monkeypatch,
        runner,
        [
            ("POST /api/places", {"places": [GEER]}),
            (
                "POST /api/place-photos",
                {"action": "give", "cluster": 0, "place": "Geer"},
            ),
        ],
    )
    photos = locations.data_dir / "c" / "Photos"
    moved = photos / "Geer" / "renamed.jpg"
    moved.parent.mkdir()
    (photos / "IMG_0.jpg").rename(moved)
    assert run(runner, "audit").exit_code == 0
    state = _json(_map(monkeypatch, runner, [("GET /api/state", None)])[0])
    hand = state["places"][0]["hand"]  # type: ignore[index]
    assert "C:\\Photos\\Geer\\renamed.jpg" in {photo["now"] for photo in hand}
    assert all(photo["now"] for photo in hand)
    # The three photos, taken in the garden, are all Geer's: no cluster is left.
    rows = cast("list[list[int]]", state["clusters"])
    assert sum(row[2] + row[3] for row in rows) == 0
