"""The people page: every face of a group, its photos set aside, moved by `clean`."""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.people.app import PeopleApp
from media_hygiene.report.decisions import read_decisions
from media_hygiene.review.http import Request
from tests.support.cli import run

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Response

JSON = {"host": "127.0.0.1:8766", "content-type": "application/json"}


def call(app: object, route: str, body: object = None) -> Response:
    """Send one request to the page app."""
    assert isinstance(app, PeopleApp)
    method, path = route.split()
    data = b"" if body is None else json.dumps(body).encode()
    return asyncio.run(app.handle(Request(method, path, JSON, data)))


def answer(app: object, route: str, body: object = None) -> dict[str, object]:
    """The JSON answer of one request."""
    result = json.loads(call(app, route, body).body)
    assert isinstance(result, dict)
    return result


def largest(app: object) -> dict[str, object]:
    """The first group of the page."""
    sections = answer(app, "GET /api/groups")["sections"]
    assert isinstance(sections, list)
    first = sections[0]
    assert isinstance(first, dict)
    return first


def every_face(app: object, section: dict[str, object]) -> list[int]:
    """The numbers of every face of a group, as the page asks for them."""
    shown = section["shown"]
    assert isinstance(shown, list)
    faces = answer(app, f"GET /api/section/{shown[0]['key']}")["faces"]
    assert isinstance(faces, list)
    return [face["key"] for face in faces]


def test_every_face_of_a_group_beyond_its_sample(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """The page shows a sample; the group's route lists every face of it."""
    monkeypatch.setattr("media_hygiene.people.views.SHOWN", 2)
    assert run(cli, "people").exit_code == 0
    section = largest(apps[-1])
    assert section["faces"] == 4
    assert len(section["shown"]) == 2  # type: ignore[arg-type]
    assert len(every_face(apps[-1], section)) == 4
    for unknown in ("99", "x"):
        assert answer(apps[-1], f"GET /api/section/{unknown}") == {"faces": []}


def test_the_photos_of_a_group_are_set_aside_read_back_and_taken_back(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """Every photo of the faces kept, once each; read back; taken out again."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    section = largest(app)
    assert section["aside"] == 0
    faces = every_face(app, section)
    kept = faces[1:]  # the first one is somebody else's: its cross took it out
    added = answer(
        app, "POST /api/aside", {"action": "add", "faces": kept, "label": "Ex"}
    )
    said = added["aside"]
    assert isinstance(said, dict)
    assert said["count"] == len(kept)
    assert "clean --decisions" in said["message"]
    assert added["chosen"] == len(kept)
    assert largest(app)["aside"] == len(kept)
    chosen = read_decisions(locations.reports_dir / "decisions.json").chosen
    assert len(chosen) == len(kept)
    assert {file.found_by for file in chosen} == {"Ex"}
    back = answer(app, "POST /api/aside", {"action": "remove", "faces": faces})
    assert back["aside"] == {"count": 0, "size": "0", "message": "Nothing set aside."}
    assert largest(app)["aside"] == 0


def test_a_wrong_body_or_no_reports_folder_saves_nothing(
    cli: CliRunner, apps: list[object], monkeypatch: pytest.MonkeyPatch
) -> None:
    """400 for a body that is not a choice; 409, said, without /reports."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    for wrong in ({"action": "delete", "faces": faces}, {"action": "add", "faces": []}):
        assert call(app, "POST /api/aside", wrong).status is HTTPStatus.BAD_REQUEST
    monkeypatch.delenv("MEDIA_HYGIENE_REPORTS_DIR")
    assert run(cli, "people").exit_code == 0
    refused = call(apps[-1], "POST /api/aside", {"action": "add", "faces": faces})
    assert refused.status is HTTPStatus.CONFLICT
    assert "/reports" in json.loads(refused.body)["error"]


def test_clean_moves_the_photos_set_aside_and_undo_brings_them_back(
    cli: CliRunner, apps: list[object], locations: Locations
) -> None:
    """The command proposes `clean --decisions`; it moves exactly those photos."""
    assert run(cli, "people").exit_code == 0
    app = apps[-1]
    faces = every_face(app, largest(app))
    answer(app, "POST /api/aside", {"action": "add", "faces": faces})
    shown = run(cli, "people")  # a new page: the console proposes the clean
    assert "clean --decisions" in shown.output.split("What next")[-1]
    photos = set(locations.data_dir.rglob("IMG_*.png"))
    result = run(cli, "clean", "--yes", "--decisions", "decisions.json")
    assert result.exit_code == 0, result.output
    left = set(locations.data_dir.rglob("IMG_*.png"))
    assert isinstance(app, PeopleApp)
    aside = {app.roster.board.faces[key].path for key in faces}
    assert len(aside) == len(faces)
    assert not aside & left  # their duplicates may go too: the same clean
    assert run(cli, "undo").exit_code == 0
    assert set(locations.data_dir.rglob("IMG_*.png")) == photos
