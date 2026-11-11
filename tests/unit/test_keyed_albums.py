"""0657: the albums API of the phone page and `/person`; 0660: ▶ Slideshow ▾ there.

A key of these pages names a file only through the page's own table and the index:
an unknown key, a path sent by the page, a file the index does not hold name nothing.
"""

from __future__ import annotations

import asyncio
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.person import door as person_door
from media_hygiene.person.albums import with_albums
from media_hygiene.person.shelf import FaceShelf, ShelfFace
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import Request, Response
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services.keyed_albums import keyed_albums
from media_hygiene.services.phone_review import phone_page
from media_hygiene.services.slideshow_selection import started_at
from media_hygiene.share.album_route import WithAlbums
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

_LOCAL = {"host": "127.0.0.1:8088", "content-type": "application/json"}


def _runtime(tmp_path: Path) -> tuple[Runtime, list[Path]]:
    runtime = make_runtime(make_locations(tmp_path))
    folder = tmp_path / "photos"
    indexed_photos(runtime.locations.index_file, folder, 2)
    return runtime, sorted(folder.iterdir())


def _post(desk_answer: WithAlbums, body: dict[str, object]) -> Response:
    request = Request("POST", desk_answer.path, _LOCAL, json.dumps(body).encode())
    return asyncio.run(desk_answer.handle(request))


class _Elsewhere:
    async def handle(self, request: Request) -> Response:
        """Answer any request as the page behind the albums would."""
        del request
        return Response(HTTPStatus.IM_A_TEAPOT)


def test_a_phone_key_names_its_copy_only_when_indexed(tmp_path: Path) -> None:
    """Key 0 an indexed copy, 1 a copy outside the index; a path and 9 name nothing."""
    runtime, photos = _runtime(tmp_path)
    outside = tmp_path / "outside.jpg"
    outside.write_bytes(photos[0].read_bytes())
    copies = {"0": photos[0], "1": outside}
    page = WithAlbums(_Elsewhere(), keyed_albums(runtime, copies.get), "/api/albums")
    keys = ["0", "1", str(photos[1]), "9"]
    answer = _post(page, {"action": "add", "album": "Crete", "keys": keys})
    assert answer.status is HTTPStatus.OK
    saved = json.loads((runtime.locations.reports_dir / "albums.json").read_text())
    text = json.dumps(saved)
    assert photos[0].name in text
    assert "outside.jpg" not in text
    assert photos[1].name not in text


def test_the_route_answers_its_path_and_passes_the_rest(tmp_path: Path) -> None:
    """GET its path: the albums; another path: the page; another host: 403."""
    runtime, _photos = _runtime(tmp_path)
    page = WithAlbums(
        _Elsewhere(), keyed_albums(runtime, lambda _key: None), "/person/api/albums"
    )
    asked = Request("GET", "/person/api/albums", _LOCAL)
    assert asyncio.run(page.handle(asked)).status is HTTPStatus.OK
    other = Request("GET", "/person", _LOCAL)
    assert asyncio.run(page.handle(other)).status is HTTPStatus.IM_A_TEAPOT
    far = Request("GET", "/person/api/albums", {"host": "evil.example"})
    assert asyncio.run(page.handle(far)).status is HTTPStatus.FORBIDDEN


def test_person_faces_reach_the_slideshow(tmp_path: Path) -> None:
    """The face picked names its photo; `tv` shows exactly it once the slot is given."""
    runtime, photos = _runtime(tmp_path)
    shown: list[tuple[Path, ...]] = []

    def tv(files: tuple[Path, ...]) -> Response:
        shown.append(files)
        return Response(HTTPStatus.OK)

    with ThreadPoolExecutor(1) as executor:
        app = person_door.person_app(runtime, executor)
    shelf: FaceShelf = app.finder.shelf
    key = shelf.add(ShelfFace(photos[1], b"v"))
    door = EndingDoor(_Elsewhere(), Ending(), person=with_albums(app, runtime))
    given = person_door.person_on_tv(door, tv)
    assert isinstance(given.person, WithAlbums)
    answer = _post(given.person, {"action": "tv", "keys": [str(key), "7"]})
    assert answer.status is HTTPStatus.OK
    assert shown == [(photos[1],)]


def test_the_bars_offer_the_album_and_the_slideshow_where_served() -> None:
    """Phone page: the album, no slideshow (own server); /person: both, served home."""
    phone = phone_page(DecisionsPlace(argument="d.json", host="d.json"))()
    assert b'id="albumBar"' in phone
    assert b'id="showBar"' not in phone
    alone = person_door.person_page(None)
    assert b'id="albumBar"' in alone
    assert b'id="showBar"' not in alone
    home = person_door.person_page(None, tv=True)
    assert b'id="showBar"' in home
    assert b'data-path="/person/api/albums"' in home


def test_on_this_pc_leads_to_the_screen() -> None:
    """The home page's 🖥 On this PC: the screen in this tab; else the remote (0660)."""
    assert started_at("here=1") == "/slideshow/screen?here=1"
    assert started_at("x=2&here=1") == "/slideshow/screen?here=1"
    assert started_at("") == "/slideshow/"
