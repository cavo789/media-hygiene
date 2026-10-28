"""0417: the slideshow served by the home server, the TV paired once for every show.

An album's show starts under `/slideshow/` without stopping the home server; the TV
comes by the plain door at `/screen`, waits while nothing is shown, and stays paired
when another album replaces the show; the PC's step and a phone's lead to the page.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from concurrent.futures import ThreadPoolExecutor
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.album_show import album_answer, shown_here
from media_hygiene.review.doors import LAN_CA_PORT
from media_hygiene.review.doors import Door as SocketDoor
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_paths import phone_may
from media_hygiene.review.lan_phones import PhoneBook
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services import slideshow_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.slideshow_here import SlideshowHere
from media_hygiene.services.slideshow_pick import Picked
from media_hygiene.slideshow.door import Door
from media_hygiene.slideshow.screens import SCREEN_COOKIE, Screens
from media_hygiene.slideshow.slides import Slide
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.services.runtime import Runtime

_ADDRESS: Final = "10.0.0.5"
_ACCESS: Final = LanAccess(_ADDRESS, 8088, b"cd" * 32)
_PC: Final = {"host": "127.0.0.1:8088"}
_TV_HOST: Final = f"{_ADDRESS}:{LAN_CA_PORT}"
_NO_ALBUM: Final = "No album named so."
_ALBUMS: Final = {"Crete": (1, 2), "Rome": (3,)}


@pytest.fixture
def here(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[SlideshowHere]:
    """The home server's slideshow over an index of three photos; two albums."""
    index = tmp_path / "index.sqlite"
    indexed_photos(index, tmp_path, 4)

    @contextlib.contextmanager
    def opened(_runtime: Runtime, *, words: bool) -> Iterator[SearchIndex]:
        assert not words
        with SearchIndex.open(index) as search:
            yield search

    def picked(_runtime: Runtime, _search: SearchIndex, pick: object) -> Picked:
        album = getattr(pick, "album", "")
        if album not in _ALBUMS:
            raise MediaHygieneError(_NO_ALBUM)
        slides = tuple(Slide(key) for key in _ALBUMS[album])
        return Picked(slides, len(slides))

    monkeypatch.setattr(slideshow_here, "open_search", opened)
    monkeypatch.setattr(slideshow_here, "shown_slides", picked)
    runtime = make_runtime(make_locations(tmp_path))
    with ThreadPoolExecutor(1) as executor:
        server = HomeServer(None, Ending(), executor, _ACCESS)
        built = SlideshowHere(FreshRuntime(runtime), server)
        yield built
        built.close()


def _pc(here: SlideshowHere, path: str, body: object = None) -> Response:
    if body is None:
        return asyncio.run(here.handle(Request("GET", path, _PC)))
    headers = _PC | {
        "content-type": "application/json",
        "origin": "http://127.0.0.1:8088",
    }
    request = Request("POST", path, headers, json.dumps(body).encode())
    return asyncio.run(here.handle(request))


def _tv(here: SlideshowHere, path: str, token: str = "") -> Response:
    headers = {"host": _TV_HOST} | (
        {"cookie": f"{SCREEN_COOKIE}={token}"} if token else {}
    )
    return asyncio.run(here.tv(Request("GET", path, headers, b"", SocketDoor.LAN)))


def _token(answer: Response) -> str:
    line = next(line for line in answer.headers if line.startswith("Set-Cookie:"))
    return line.split(f"{SCREEN_COOKIE}=", 1)[1].split(";", 1)[0]


def test_an_album_starts_in_the_home_server_and_opens_its_remote(
    here: SlideshowHere,
) -> None:
    """`/slideshow/album/Crete`: 303 to the remote, which then serves the show."""
    assert _pc(here, "/slideshow/").status is HTTPStatus.NOT_FOUND  # nothing yet
    assert _pc(here, "/slideshow").status is HTTPStatus.SEE_OTHER
    started = _pc(here, "/slideshow/album/Crete")
    assert started.status is HTTPStatus.SEE_OTHER
    assert "Location: /slideshow/" in started.headers
    remote = _pc(here, "/slideshow/")
    assert remote.status is HTTPStatus.OK
    assert b'"api/slides"' in remote.body  # its addresses are relative
    slides = json.loads(_pc(here, "/slideshow/api/slides").body)["slides"]
    assert [slide["thumb"] for slide in slides] == ["thumb/1.jpg", "thumb/2.jpg"]
    assert _pc(here, "/slideshow/thumb/1.jpg").status is HTTPStatus.OK
    missing = _pc(here, "/slideshow/album/Nowhere")
    assert missing.status is HTTPStatus.CONFLICT
    assert b"No album named so." in missing.body


def test_the_tv_paired_once_follows_the_next_album(here: SlideshowHere) -> None:
    """The TV waits, shows its code, is paired, and keeps its pairing for Rome."""
    waiting = _tv(here, "/screen")
    assert waiting.status is HTTPStatus.OK
    assert b'http-equiv="refresh"' in waiting.body
    assert _tv(here, "/").status is HTTPStatus.SEE_OTHER  # the phones' steps
    _pc(here, "/slideshow/album/Crete")
    page = _tv(here, "/screen")
    token = _token(page)
    code = json.loads(_tv(here, "/api/wait/0", token).body)["code"]
    paired = _pc(here, "/slideshow/api/screens", {"code": code})
    assert paired.status is HTTPStatus.OK
    shown = json.loads(_tv(here, "/api/wait/0", token).body)
    assert shown["photo"] == "tv/1.jpg"
    version = shown["version"]
    _pc(here, "/slideshow/album/Rome")
    moved = json.loads(_tv(here, f"/api/wait/{version}", token).body)
    assert moved["photo"] == "tv/3.jpg"  # no new code: still paired
    assert moved["version"] > version
    assert _tv(here, "/tv/3.jpg", token).status is HTTPStatus.OK
    forged = Request("GET", "/screen", {"host": "evil.example"}, b"", SocketDoor.LAN)
    assert asyncio.run(here.tv(forged)).status is HTTPStatus.FORBIDDEN


def test_the_step_of_an_album_is_a_page_of_the_home_server() -> None:
    """The PC's form and a phone's tap lead to `/slideshow/album/<name>`."""
    assert shown_here("slideshow-album", {"album": "Crete 2023"}) == (
        "/slideshow/album/Crete%202023"
    )
    assert shown_here("slideshow-album", {"album": " "}) is None
    assert shown_here("search", {}) is None
    answer = album_answer("slideshow-album", {"album": "Rome"})
    assert answer is not None
    assert json.loads(answer.body) == {"page": "/slideshow/album/Rome"}


def test_a_phone_drives_the_show_but_never_reads_the_code() -> None:
    """0417 widens the phone's list deliberately: the show in memory, never a file."""
    headers = {"host": _ACCESS.host, "cookie": f"{COOKIE_NAME}={_ACCESS.token}"}

    def may(method: str, path: str) -> bool:
        return phone_may(Request(method, path, headers, b"", SocketDoor.LAN))

    assert may("GET", "/slideshow/")
    assert may("GET", "/slideshow/album/Crete")
    assert may("POST", "/slideshow/api/show")
    assert may("POST", "/slideshow/api/screens")
    assert not may("GET", "/slideshow/api/lan")  # the code stays on the PC
    assert not any(path.startswith("/slideshow/") for path in CHANGES)


def test_a_phone_paired_on_the_slideshow_is_paired_for_good(tmp_path: Path) -> None:
    """Consistent with 0431: the right code on `slideshow --lan` writes phones.json."""
    secure = LanAccess(_ADDRESS, 8088, b"cd" * 32, secure=True)
    phones = PhoneBook(tmp_path)
    door = Door(secure, Screens(), phones=phones)
    headers = {"host": secure.host, "user-agent": "Mozilla/5.0 (Linux; Android 14)"}
    typed = secure.shown_code.replace(" ", "")
    answer = door.pair_phone(
        Request("GET", f"/pair/{typed}", headers, b"", SocketDoor.LAN)
    )
    assert answer.status is HTTPStatus.SEE_OTHER
    cookie = next(line for line in answer.headers if line.startswith("Set-Cookie:"))
    assert "Max-Age=" in cookie
    assert "Secure" in cookie
    assert len(phones.listed()) == 1
    wrong = door.pair_phone(Request("GET", "/pair/0", headers, b"", SocketDoor.LAN))
    assert wrong.status is HTTPStatus.FORBIDDEN
    assert len(phones.listed()) == 1
