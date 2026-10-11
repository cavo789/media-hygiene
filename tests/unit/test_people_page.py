"""The people page: groups by number, faces cut on request, read-only, local only."""

from __future__ import annotations

import asyncio
import io
import json
from http import HTTPStatus
from typing import TYPE_CHECKING

from PIL import Image

from media_hygiene.faces.models import FaceBox
from media_hygiene.index.face_rows import StoredFace
from media_hygiene.paths.host_paths import HostPathMapper
from media_hygiene.people.app import PeopleApp
from media_hygiene.people.board import PeopleBoard
from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.review.http import Request
from media_hygiene.services.people_groups import PeopleGroups
from tests.support.faces import coloured
from tests.support.runtime import thread_pool

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Response

LOCAL = {"host": "127.0.0.1:8088"}


def stored(path: Path, number: int = 0) -> StoredFace:
    """A face filling most of a 96 x 64 picture."""
    return StoredFace(path, number, FaceBox(20, 10, 40, 40), 0.95, 50.0, b"")


def board_of(tmp_path: Path) -> PeopleBoard:
    """Two groups of two faces, plus one face alone; the second photo is gone."""
    first = coloured(tmp_path / "data" / "a.png", 0)
    gone = tmp_path / "data" / "gone.png"
    groups = (
        (stored(first), stored(first, 1)),
        (stored(first, 2), stored(gone)),
        (stored(first, 3),),
    )
    return PeopleBoard.of(PeopleGroups(groups, too_small=0, too_blurry=0))


def ask(app: PeopleApp, route: str, headers: dict[str, str] | None = None) -> Response:
    """Send one request to the app."""
    method, path = route.split()
    return asyncio.run(app.handle(Request(method, path, headers or LOCAL)))


def test_the_page_lists_the_groups_and_cuts_the_faces(tmp_path: Path) -> None:
    """Groups of two or more by number, the host path shown; faces and photos served."""
    board = board_of(tmp_path)
    mapper = HostPathMapper(tmp_path / "data")
    with thread_pool() as executor:
        app = PeopleApp(board, mapper, b"<html>", executor)
        assert ask(app, "GET /").body == b"<html>"
        state = json.loads(ask(app, "GET /api/groups").body)
        assert state["alone"] == 1
        assert [group["faces"] for group in state["groups"]] == [2, 2]
        assert [group["photos"] for group in state["groups"]] == [1, 2]
        assert [face["key"] for face in state["groups"][1]["shown"]] == [2, 3]
        face = ask(app, "GET /face/0.jpg")
        assert face.status is HTTPStatus.OK
        assert face.body.startswith(b"\xff\xd8")
        assert ask(app, "GET /photo/0.jpg").status is HTTPStatus.OK
        for missing in ("/face/3.jpg", "/photo/3.jpg", "/face/9.jpg", "/face/x.jpg"):
            assert ask(app, f"GET {missing}").status is HTTPStatus.NOT_FOUND
        assert ask(app, "GET /other.jpg").status is HTTPStatus.NOT_FOUND
        assert ask(app, "GET /nothing").status is HTTPStatus.NOT_FOUND
        assert ask(app, "POST /api/groups").status is HTTPStatus.METHOD_NOT_ALLOWED
        foreign = ask(app, "GET /", {"host": "example.com"})
        assert foreign.status is HTTPStatus.FORBIDDEN


def test_a_face_is_cut_square_with_its_surroundings(tmp_path: Path) -> None:
    """The crop is a small square JPEG, even for a face at the edge."""
    picture = coloured(tmp_path / "a.png", 1, (300, 200))
    crop = face_crop(CropJob(picture, FaceBox(250, 150, 50, 50)))
    assert crop is not None
    with Image.open(io.BytesIO(crop)) as image:
        assert image.size[0] == image.size[1] <= 160
