"""An album on a phone at home (0297); a paired phone changing an album (0295, 4).

The albums' page in front of the home page, behind the door of `mh --lan`: a paired
phone lists the albums, opens one (cover, days, its pictures), takes a photo out or adds
it to another album; it never reaches a file of no album, an original, nor a step.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override
from urllib.parse import quote

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.local_app import LocalApp
from media_hygiene.services.album_pages import album_pages
from media_hygiene.services.albums import album_store
from media_hygiene.share.album_store import AlbumChange
from media_hygiene.share.albums import ALBUMS_FILE, read_albums
from tests.support.cli import run
from tests.support.runtime import make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations
    from media_hygiene.services.runtime import Runtime

_PORT: Final = 8765
_HOST: Final = f"192.168.1.20:{_PORT}"
_ORIGIN: Final = f"http://{_HOST}"
_ACCESS: Final = LanAccess("192.168.1.20", _PORT, b"cd" * 32)
_ALBUM: Final = "Crete 2023"
_JPEG: Final = ".jpg"


class _Home(LocalApp):
    """Stands for the home page: answers 200 to whatever it is passed."""

    __slots__ = ("seen",)

    def __init__(self) -> None:
        """Start without any request."""
        self.seen: list[str] = []

    @override
    async def answer(self, request: Request) -> Response:
        """Keep the path, answer 200."""
        self.seen.append(request.path)
        return Response(HTTPStatus.OK, b"home")


@pytest.fixture
def phone_door(
    cli: CliRunner, locations: Locations
) -> Iterator[tuple[LanApp, _Home, Runtime]]:
    """The demo tree audited, an album of two photos, the door of `mh --lan`."""
    assert run(cli, "audit").exit_code == 0
    runtime = make_runtime(locations)
    photos = _photos(runtime)
    album_store(runtime).add(AlbumChange(_ALBUM, (photos[0][1], photos[1][1])))
    home = _Home()
    with ThreadPoolExecutor(2) as pool:
        pages = album_pages(runtime, home, pool)
        yield LanApp(pages, _ACCESS, b"<p>phone</p>"), home, runtime


def _photos(runtime: Runtime) -> list[tuple[int, Path]]:
    """The demo tree's JPEG photos the index knows, by key."""
    index = runtime.index_file
    assert index is not None
    with closing(sqlite3.connect(index)) as connection:
        rows = connection.execute("SELECT rowid, path FROM files ORDER BY path")
        found = [(int(key), runtime.mapper.to_container(path)) for key, path in rows]
    return [(key, path) for key, path in found if path.suffix.lower() == _JPEG]


def _ask(door: LanApp, request: Request) -> Response:
    return asyncio.run(EndingDoor(door, Ending()).handle(request))


def _phone(path: str, body: object = None, *, paired: bool = True) -> Request:
    """A request of the phone; a body makes it a `POST` of the page."""
    headers = {"host": _HOST}
    if paired:
        headers["cookie"] = f"{COOKIE_NAME}={_ACCESS.token}"
    if body is None:
        return Request("GET", path, headers, door=Door.LAN)
    headers |= {"content-type": ContentType.JSON, "origin": _ORIGIN}
    return Request("POST", path, headers, json.dumps(body).encode(), Door.LAN)


def _json(reply: Response) -> dict[str, object]:
    assert reply.status == HTTPStatus.OK, reply.body
    loaded: dict[str, object] = json.loads(reply.body)
    return loaded


def _album(door: LanApp) -> dict[str, object]:
    return _json(_ask(door, _phone(f"/api/album/{quote(_ALBUM.lower())}")))


def _keys(view: dict[str, object]) -> list[int]:
    days = view["days"]
    assert isinstance(days, list)
    return [item["key"] for day in days for item in day["items"]]


def test_a_paired_phone_lists_the_albums_and_opens_one(
    phone_door: tuple[LanApp, _Home, Runtime],
) -> None:
    """The page, the list (cover, count), an album by day, its two pictures."""
    door, home, _runtime = phone_door
    page = _ask(door, _phone("/albums"))
    assert page.status == HTTPStatus.OK
    assert b"/api/album-list" in page.body
    listed = _json(_ask(door, _phone("/api/album-list")))["albums"]
    assert isinstance(listed, list)
    assert [(each["name"], each["count"]) for each in listed] == [(_ALBUM, 2)]
    assert "days" not in listed[0]
    view = _album(door)
    keys = _keys(view)
    cover = view["cover"]
    assert isinstance(cover, dict)
    assert cover["key"] in keys
    for key in keys:
        for prefix in ("/thumb/", "/tv/"):
            reply = _ask(door, _phone(f"{prefix}{key}{_JPEG}"))
            assert reply.status == HTTPStatus.OK, prefix
            assert reply.body.startswith(b"\xff\xd8")
    assert not home.seen  # nothing of the albums reached the home page
    assert _ask(door, _phone("/api/album/Nowhere")).status == HTTPStatus.NOT_FOUND


def test_a_phone_never_reaches_a_file_of_no_album(
    phone_door: tuple[LanApp, _Home, Runtime],
) -> None:
    """Another photo by the albums' paths, an original: never served."""
    door, _home, runtime = phone_door
    shown = set(_keys(_album(door)))
    other = next(key for key, _path in _photos(runtime) if key not in shown)
    for path in (f"/thumb/{other}{_JPEG}", f"/tv/{other}{_JPEG}", f"/film/{other}.mp4"):
        assert _ask(door, _phone(path)).status == HTTPStatus.NOT_FOUND, path
    kept = next(iter(shown))
    original = _ask(door, _phone(f"/original/{kept}{_JPEG}"))
    assert original.status == HTTPStatus.FORBIDDEN  # search's previews pass (0360)
    unpaired = _ask(door, _phone("/api/album-list", paired=False))
    assert unpaired.status == HTTPStatus.UNAUTHORIZED


def test_the_pc_gets_the_search_thumbnail_of_a_file_of_no_album(
    phone_door: tuple[LanApp, _Home, Runtime],
) -> None:
    """`search` and `browse` share `/thumb/`: another key goes on to them (0356)."""
    door, home, runtime = phone_door
    shown = set(_keys(_album(door)))
    other = next(key for key, _path in _photos(runtime) if key not in shown)
    local = {"host": f"127.0.0.1:{_PORT}"}
    reply = _ask(door, Request("GET", f"/thumb/{other}{_JPEG}", local))
    assert (reply.status, reply.body) == (HTTPStatus.OK, b"home")
    assert home.seen == [f"/thumb/{other}{_JPEG}"]
    kept = next(iter(shown))
    reply = _ask(door, Request("GET", f"/thumb/{kept}{_JPEG}", local))
    assert reply.body.startswith(b"\xff\xd8")
    assert len(home.seen) == 1  # an album's file: still the albums' own


def test_a_paired_phone_changes_an_album_and_nothing_else(
    phone_door: tuple[LanApp, _Home, Runtime],
) -> None:
    """Out of the album, into another one, read back; a file of no album is dropped."""
    door, _home, runtime = phone_door
    first, second = _keys(_album(door))
    other = next(key for key, _path in _photos(runtime) if key not in {first, second})
    added = _json(
        _ask(
            door,
            _phone(
                "/api/albums",
                {"action": "add", "album": "Kids", "keys": [str(first), str(other)]},
            ),
        )
    )
    assert "Only this file changed" in str(added["message"])
    taken = {"action": "remove", "album": _ALBUM, "keys": [str(second)]}
    _json(_ask(door, _phone("/api/albums", taken)))
    saved = read_albums(runtime.locations.reports_dir / ALBUMS_FILE)
    counts = {album.name: len(album.entries) for album in saved.albums}
    assert counts == {_ALBUM: 1, "Kids": 1}  # the file of no album never entered
    evil = _phone("/api/albums", taken)
    evil = Request(evil.method, evil.path, {**evil.headers, "origin": "http://evil"})
    assert _ask(door, evil).status == HTTPStatus.FORBIDDEN
