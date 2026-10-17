"""`places`: the first photos of a cluster, to recognise the place before naming it.

TODO 0226. The garden's three photos are one cluster; its previews are rendered from
the folders mounted read-only; a photo moved since the audit is missing, not an error.
TODO 0233: each photo names its folder as a host path; the viewer's larger preview.
"""

from __future__ import annotations

import json
from typing import TYPE_CHECKING, Final

from media_hygiene.services import places as places_service
from tests.support.cli import run
from tests.support.places_map import audited_garden, call, fake_server

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.places.app import PlacesApp
    from media_hygiene.review.http import Response

JPEG_START: Final = b"\xff\xd8"


def _answers(
    monkeypatch: pytest.MonkeyPatch, runner: CliRunner, routes: list[str]
) -> list[Response]:
    """Open the map, ask the first cluster's photos, then each route given."""
    seen: list[Response] = []

    async def act(app: PlacesApp) -> None:
        listed = await call(app, "GET /api/cluster/0")
        seen.append(listed)
        photos = json.loads(listed.body)["photos"]
        seen.append(await call(app, f"GET {photos[0]['preview']}"))
        seen.extend([await call(app, route) for route in routes])

    monkeypatch.setattr(places_service, "run_server", fake_server(act))
    result = run(runner, "places")
    assert result.exit_code == 0, result.output
    return seen


def test_the_photos_of_a_cluster_are_listed_and_previewed(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Three photos, each with its position; the first preview is a JPEG."""
    runner = audited_garden(locations, monkeypatch)
    listed, preview, *_rest = _answers(monkeypatch, runner, [])

    photos = json.loads(listed.body)["photos"]
    assert sorted(photo["name"] for photo in photos) == [
        "IMG_0.jpg",
        "IMG_1.jpg",
        "IMG_2.jpg",
    ]
    assert all(photo["found"] for photo in photos)
    assert all(photo["latitude"] and photo["longitude"] for photo in photos)
    assert preview.status == 200
    assert preview.body.startswith(JPEG_START)


def test_an_unknown_cluster_or_key_is_not_found(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """A rank beyond the clusters, a word, a key never listed: 404, never an error."""
    runner = audited_garden(locations, monkeypatch)
    routes = [
        "GET /api/cluster/7",
        "GET /api/cluster/first",
        "GET /preview/0123456789abcdef01234567.jpg",
    ]
    answers = _answers(monkeypatch, runner, routes)

    assert [answer.status for answer in answers[2:]] == [404, 404, 404]


def test_a_photo_moved_since_the_audit_is_missing_not_an_error(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Renamed in Explorer after the audit: listed as not found, its preview 404."""
    runner = audited_garden(locations, monkeypatch)
    folder = locations.data_dir / "c/Photos"
    for photo in folder.glob("IMG_*.jpg"):
        photo.rename(photo.with_name(f"renamed_{photo.name}"))
    listed, preview, *_rest = _answers(monkeypatch, runner, [])

    photos = json.loads(listed.body)["photos"]
    assert photos
    assert not any(photo["found"] for photo in photos)
    assert preview.status == 404


def test_each_photo_names_its_host_folder_and_has_a_larger_preview(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    r"""`C:\Photos`, as the user knows it; the viewer's preview is a JPEG too."""
    runner = audited_garden(locations, monkeypatch)
    seen: list[Response] = []

    async def act(app: PlacesApp) -> None:
        listed = await call(app, "GET /api/cluster/0")
        first = json.loads(listed.body)["photos"][0]
        seen.extend([listed, await call(app, f"GET {first['large']}")])

    monkeypatch.setattr(places_service, "run_server", fake_server(act))
    assert run(runner, "places").exit_code == 0
    listed, large = seen[0], seen[1]
    photos = json.loads(listed.body)["photos"]
    assert {photo["folder"] for photo in photos} == {"C:\\Photos"}
    assert not any(photo["video"] for photo in photos)
    assert large.status == 200
    assert large.body.startswith(JPEG_START)


def test_the_state_counts_pictures_and_videos_apart(
    locations: Locations, monkeypatch: pytest.MonkeyPatch
) -> None:
    """TODO 0232: each cluster is (latitude, longitude, pictures, videos, place)."""
    runner = audited_garden(locations, monkeypatch)
    seen: list[Response] = []

    async def act(app: PlacesApp) -> None:
        seen.append(await call(app, "GET /api/state"))

    monkeypatch.setattr(places_service, "run_server", fake_server(act))
    assert run(runner, "places").exit_code == 0
    [(_latitude, _longitude, pictures, videos, place)] = json.loads(seen[0].body)[
        "clusters"
    ]
    assert (pictures, videos, place) == (3, 0, "")
