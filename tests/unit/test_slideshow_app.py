"""The slideshow's server (0291): who may ask what, the TV paired the other way round.

The PC (loopback) does everything; under `mh --lan` a request naming the PC's address
on the home network is a phone paired by the run's code (0269), a TV paired by the
code it shows, or a stranger who sees only the pairing pages; any other host is
refused. Only the show's photos are served, never an original.
"""

from __future__ import annotations

import asyncio
import json
import sqlite3
from concurrent.futures import ThreadPoolExecutor
from contextlib import closing
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, NamedTuple

import pytest
from PIL import Image

from media_hygiene.index.schema import prepare
from media_hygiene.review.doors import LAN_CA_PORT
from media_hygiene.review.doors import Door as SocketDoor
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess, lan_access
from media_hygiene.review.lan_address import LAN_ADDRESS_VARIABLE
from media_hygiene.review.lan_ca_page import CA_DOWNLOAD, PHONE_STEPS, CaDoor
from media_hygiene.review.lan_card import lan_response
from media_hygiene.review.lan_phones import PhoneBook
from media_hygiene.review.lan_tls import certificates, secure_door
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.pictures import Pictures
from media_hygiene.slideshow.app import ShowPages, SlideshowApp
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.door import Door, Visitor
from media_hygiene.slideshow.pictures import ShowPictures
from media_hygiene.slideshow.screen_jpeg import ScreenJob
from media_hygiene.slideshow.screens import MAX_FAILURES, SCREEN_COOKIE, Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing
from media_hygiene.slideshow.tv_door import TvDoor

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

_TV_PORT: Final = 8090
_PC_ADDRESS: Final = "10.0.0.5"
_ACCESS: Final = LanAccess(_PC_ADDRESS, _TV_PORT, b"cd" * 32)
_LAN_HOST: Final = _ACCESS.host
_REMOTE: Final = b"<p>remote</p>"
_SCREEN: Final = b"<p>screen</p>"
_JSON: Final = "application/json"
_SHOWN_KEYS: Final = (1, 2)  # the third photo of the index is not in the show


@pytest.fixture
def app(tmp_path: Path) -> Iterator[SlideshowApp]:
    """A show of two photos out of the three of an index, the PC on the home network."""
    index = tmp_path / "index.sqlite"
    with closing(sqlite3.connect(index)) as connection:
        prepare(connection)
        for number in range(3):
            photo = tmp_path / f"IMG_{number}.jpg"
            Image.new("RGB", (64, 48), (number * 80, 0, 0)).save(photo)
            connection.execute(
                "INSERT INTO files (path, size, mtime_ns) VALUES (?, ?, ?)",
                (str(photo), photo.stat().st_size, 1),
            )
        connection.commit()
    show = Show(tuple(Slide(key) for key in _SHOWN_KEYS), Timing(8.0))
    screens = Screens()
    with SearchIndex.open(index) as search, ThreadPoolExecutor(1) as executor:
        pictures = ShowPictures(
            frozenset(_SHOWN_KEYS),
            Pictures(search, None, executor),
            ScreenJob(640, None),
            executor,
        )
        yield SlideshowApp(
            Desk(show, screens, Changes()),
            Door(_ACCESS, screens),
            ShowPages(_REMOTE, _SCREEN),
            pictures,
        )


def _ask(app: SlideshowApp, request: Request) -> Response:
    """Ask through the door every page has, as the server does."""
    return asyncio.run(EndingDoor(app, Ending()).handle(request))


class _Sender(NamedTuple):
    """Who sends a request: the `Host` it names, the cookie it holds."""

    host: str
    cookie: str = ""


_PHONE_COOKIE: Final = f"{COOKIE_NAME}={_ACCESS.token}"
_PC: Final = _Sender(f"127.0.0.1:{_TV_PORT}")
_STRANGER: Final = _Sender(_LAN_HOST)
_PHONE: Final = _Sender(_LAN_HOST, _PHONE_COOKIE)


def _request(path: str, sender: _Sender = _STRANGER, body: object = None) -> Request:
    headers = {"host": sender.host}
    door = (
        SocketDoor.PC if sender is _PC else SocketDoor.LAN
    )  # the socket, as the server marks it
    if sender.cookie:
        headers["cookie"] = sender.cookie
    if body is None:
        return Request("GET", path, headers, door=door)
    headers |= {"content-type": _JSON, "origin": f"http://{sender.host}"}
    return Request("POST", path, headers, json.dumps(body).encode(), door)


def test_the_pc_does_everything_without_pairing(app: SlideshowApp) -> None:
    """The remote, the show, an action, the pictures, the LAN card: the loopback."""
    assert _ask(app, _request("/", sender=_PC)).body == _REMOTE
    slides = json.loads(_ask(app, _request("/api/slides", sender=_PC)).body)
    assert [slide["key"] for slide in slides["slides"]] == list(_SHOWN_KEYS)
    moved = _ask(app, _request("/api/show", sender=_PC, body={"action": "next"}))
    assert json.loads(moved.body)["current"] == _SHOWN_KEYS[1]
    state = json.loads(_ask(app, _request("/api/show/0", sender=_PC)).body)
    assert state["current"] == _SHOWN_KEYS[1]
    wait = json.loads(_ask(app, _request("/api/wait/0", sender=_PC)).body)
    assert wait == {
        "version": state["version"],
        "key": 2,
        "photo": "tv/2.jpg",
        "film": "",
        "next": "tv/1.jpg",
        "playing": False,
        "code": "",
        "chapter": None,
    }
    assert _ask(app, _request("/tv/2.jpg", sender=_PC)).status is HTTPStatus.OK
    assert _ask(app, _request("/thumb/1.jpg", sender=_PC)).status is HTTPStatus.OK
    lan = json.loads(_ask(app, _request("/api/lan", sender=_PC)).body)
    assert lan["code"] == _ACCESS.shown_code
    assert "<svg" in lan["qr"]


def test_only_the_show_s_photos_are_served(app: SlideshowApp) -> None:
    """A key of the index outside the show, an original, a large preview: 404."""
    for path in (
        "/tv/3.jpg",
        "/thumb/3.jpg",
        "/tv/x.jpg",
        "/original/1.jpg",
        "/preview/1.jpg",
    ):
        assert _ask(app, _request(path, sender=_PC)).status is HTTPStatus.NOT_FOUND


def test_another_host_is_refused(app: SlideshowApp) -> None:
    """A name the PC is not known by (DNS rebinding), another address: 403."""
    for host in ("evil.example:8090", "10.0.0.6:8090", f"{_PC_ADDRESS}:9999"):
        response = _ask(app, _request("/", sender=_Sender(host, _PHONE_COOKIE)))
        assert response.status is HTTPStatus.FORBIDDEN


def test_without_mh_lan_the_home_network_is_refused(app: SlideshowApp) -> None:
    """No access given: even the PC's own address is a stranger host."""
    closed = SlideshowApp(
        app.desk, Door(None, app.desk.screens), app.pages, app.pictures
    )
    assert _ask(closed, _request("/screen")).status is HTTPStatus.FORBIDDEN
    assert _ask(closed, _request("/pair/1")).status is HTTPStatus.FORBIDDEN


def test_a_stranger_sees_the_pairing_page_only(app: SlideshowApp) -> None:
    """The remote, the show, the pictures, the LAN card: the pairing page or 403."""
    for path in (
        "/",
        "/api/slides",
        "/api/show/0",
        "/tv/1.jpg",
        "/thumb/1.jpg",
        "/api/lan",
    ):
        response = _ask(app, _request(path))
        assert response.status is HTTPStatus.UNAUTHORIZED, path
        assert b"/pair/" in response.body
    posted = _ask(app, _request("/api/show", body={"action": "next"}))
    assert posted.status is HTTPStatus.FORBIDDEN
    assert app.desk.show.current == Slide(_SHOWN_KEYS[0])


def test_the_phone_pairs_with_the_run_s_code_then_drives_the_show(
    app: SlideshowApp,
) -> None:
    """The run's code sets the cookie and opens the remote; its POST passes."""
    wrong = _ask(app, _request("/pair/00000000"))
    assert wrong.status is HTTPStatus.FORBIDDEN
    paired = _ask(app, _request(f"/pair/{_ACCESS.code}"))
    assert paired.status is HTTPStatus.SEE_OTHER
    assert "Location: /" in paired.headers
    assert any(_ACCESS.token in line for line in paired.headers)
    assert _ask(app, _request("/", sender=_PHONE)).body == _REMOTE
    moved = _ask(app, _request("/api/show", sender=_PHONE, body={"action": "next"}))
    assert moved.status is HTTPStatus.OK
    assert _ask(app, _request("/thumb/2.jpg", sender=_PHONE)).status is HTTPStatus.OK
    assert (
        _ask(app, _request("/assets/images/favicon.png", sender=_PHONE)).status
        is HTTPStatus.OK
    )
    assert _ask(app, _request("/api/lan", sender=_PHONE)).status is HTTPStatus.NOT_FOUND


def test_a_phone_s_post_from_another_site_is_refused(app: SlideshowApp) -> None:
    """The cookie rides along a page of another site: its Origin is refused."""
    request = _request("/api/show", sender=_PHONE, body={"action": "next"})
    forged = Request(
        "POST",
        request.path,
        {**request.headers, "origin": "http://evil.example"},
        request.body,
        request.door,
    )
    assert _ask(app, forged).status is HTTPStatus.FORBIDDEN
    assert app.desk.show.current == Slide(_SHOWN_KEYS[0])


def _screen_token(response: Response) -> str:
    line = next(line for line in response.headers if line.startswith("Set-Cookie:"))
    return line.split(f"{SCREEN_COOKIE}=", 1)[1].split(";", 1)[0]


def test_the_tv_shows_a_code_the_phone_types(app: SlideshowApp) -> None:
    """The TV gets a token and a code; the phone types it; the TV shows the photo."""
    page = _ask(app, _request("/screen"))
    assert page.body == _SCREEN
    token = _screen_token(page)
    tv = f"{SCREEN_COOKIE}={token}"
    waiting = json.loads(
        _ask(app, _request("/api/wait/0", sender=_Sender(_LAN_HOST, tv))).body
    )
    code = waiting["code"]
    assert len(code.replace(" ", "")) == 6
    assert (
        _ask(app, _request("/tv/1.jpg", sender=_Sender(_LAN_HOST, tv))).status
        is HTTPStatus.UNAUTHORIZED
    )
    refused = _ask(
        app,
        _request(
            "/api/screens",
            sender=_PHONE,
            body={"code": "000 000" if code != "000 000" else "111 111"},
        ),
    )
    assert refused.status is HTTPStatus.UNPROCESSABLE_ENTITY
    paired = _ask(app, _request("/api/screens", sender=_PHONE, body={"code": code}))
    assert json.loads(paired.body)["screens"] == 1
    shown = json.loads(
        _ask(app, _request("/api/wait/0", sender=_Sender(_LAN_HOST, tv))).body
    )
    assert shown["photo"] == "tv/1.jpg"
    assert (
        _ask(app, _request("/tv/1.jpg", sender=_Sender(_LAN_HOST, tv))).status
        is HTTPStatus.OK
    )
    assert (
        _ask(app, _request("/screen", sender=_Sender(_LAN_HOST, tv))).headers == ()
    )  # its token kept
    # A TV is no remote: no action, no thumbnail, no list.
    assert (
        _ask(
            app,
            _request(
                "/api/show", sender=_Sender(_LAN_HOST, tv), body={"action": "next"}
            ),
        ).status
        is HTTPStatus.FORBIDDEN
    )
    assert (
        _ask(app, _request("/thumb/1.jpg", sender=_Sender(_LAN_HOST, tv))).status
        is HTTPStatus.UNAUTHORIZED
    )
    assert (
        _ask(app, _request("/api/slides", sender=_Sender(_LAN_HOST, tv))).status
        is HTTPStatus.UNAUTHORIZED
    )


def test_a_tv_unknown_to_the_server_is_told_to_reload(app: SlideshowApp) -> None:
    """A token of a previous run: 401, the page reloads and gets a new code."""
    stale = f"{SCREEN_COOKIE}={'ab' * 32}"
    assert (
        _ask(app, _request("/api/wait/0", sender=_Sender(_LAN_HOST, stale))).status
        is HTTPStatus.UNAUTHORIZED
    )
    assert _ask(app, _request("/api/wait/0")).status is HTTPStatus.UNAUTHORIZED


def test_a_stranger_cannot_pair_a_tv(app: SlideshowApp) -> None:
    """Only a phone paired by the run's code types a TV's code."""
    tv = f"{SCREEN_COOKIE}={_screen_token(_ask(app, _request('/screen')))}"
    code = json.loads(
        _ask(app, _request("/api/wait/0", sender=_Sender(_LAN_HOST, tv))).body
    )["code"]
    response = _ask(
        app,
        _request("/api/screens", sender=_Sender(_LAN_HOST, tv), body={"code": code}),
    )
    assert response.status is HTTPStatus.FORBIDDEN
    assert app.desk.screens.paired == 0


def test_wrong_tv_codes_close_the_pairing_of_tvs() -> None:
    """After MAX_FAILURES wrong codes, even the right one is refused."""
    screens = Screens()
    token = screens.arrive("")
    assert token is not None
    code = screens.code_of(token)
    assert code is not None
    wrong = "000000" if code != "000000" else "111111"
    for _attempt in range(MAX_FAILURES):
        assert not screens.confirm(wrong)
    assert screens.closed
    assert not screens.confirm(code)
    assert screens.paired == 0


def test_waiting_tvs_are_bounded() -> None:
    """The oldest waiting TV is forgotten beyond the bound; codes never repeat."""
    screens = Screens()
    tokens = [screens.arrive("") for _tv in range(20)]
    assert all(token is not None for token in tokens)
    waiting = [screens.code_of(token or "") for token in tokens]
    assert waiting[0] is None
    kept = [code for code in waiting if code is not None]
    assert len(kept) == len(set(kept))
    assert screens.arrive(tokens[-1] or "") is None


def test_a_forged_loopback_host_by_the_lan_door_is_a_stranger(
    app: SlideshowApp,
) -> None:
    """0384: the PC's `Host` written by a device of the Wi-Fi gives no PC right."""
    forged = Request(
        "GET", "/api/slides", {"host": f"127.0.0.1:{_TV_PORT}"}, door=SocketDoor.LAN
    )
    assert app.door.visitor(forged) is not Visitor.PC


# ---- Under HTTPS: the TV by the plain door, phones paired for good (2026-10-28) ----

_TV_HOST: Final = f"{_PC_ADDRESS}:{LAN_CA_PORT}"


def _plain(path: str, cookie: str = "", method: str = "GET") -> Request:
    """A request of the plain HTTP door, marked as the home network's."""
    headers = {"host": _TV_HOST} | ({"cookie": cookie} if cookie else {})
    return Request(method, path, headers, b"", SocketDoor.LAN)


def test_the_tv_is_served_by_the_plain_door_and_the_remote_is_not(
    app: SlideshowApp, tmp_path: Path
) -> None:
    """`/` leads the TV to its page; its code, then its show and its pictures."""
    assert certificates(tmp_path, _PC_ADDRESS)
    tv = TvDoor(app)
    door = CaDoor(tmp_path, f"https://{_LAN_HOST}", tv.handle)
    home = asyncio.run(door.handle(_plain("/")))
    assert home.status is HTTPStatus.SEE_OTHER
    assert "Location: /screen" in home.headers
    page = asyncio.run(door.handle(_plain("/screen")))
    assert page.body == _SCREEN
    token = f"{SCREEN_COOKIE}={_screen_token(page)}"
    code = json.loads(asyncio.run(door.handle(_plain("/api/wait/0", token))).body)
    paired = _ask(app, _request("/api/screens", _PHONE, {"code": code["code"]}))
    assert paired.status is HTTPStatus.OK
    shown = json.loads(asyncio.run(door.handle(_plain("/api/wait/0", token))).body)
    assert shown["photo"] == "tv/1.jpg"
    picture = asyncio.run(door.handle(_plain("/tv/1.jpg", token)))
    assert picture.status is HTTPStatus.OK


def test_the_plain_door_serves_nothing_of_the_remote(
    app: SlideshowApp, tmp_path: Path
) -> None:
    """A phone's cookie on the plain door: no remote, no show moved, no pairing."""
    tv = TvDoor(app)
    door = CaDoor(tmp_path, f"https://{_LAN_HOST}", tv.handle)
    for path in ("/api/slides", "/api/show/0", "/thumb/1.jpg", "/pair/1", "/api/lan"):
        answer = asyncio.run(door.handle(_plain(path, _PHONE_COOKIE)))
        assert answer.status is HTTPStatus.NOT_FOUND, path
    posted = asyncio.run(door.handle(_plain("/api/show", _PHONE_COOKIE, "POST")))
    assert posted.status is HTTPStatus.METHOD_NOT_ALLOWED
    assert app.desk.show.current == Slide(_SHOWN_KEYS[0])
    steps = asyncio.run(door.handle(_plain(PHONE_STEPS)))
    assert CA_DOWNLOAD.encode() in steps.body
    forged = Request("GET", "/screen", {"host": _LAN_HOST}, b"", SocketDoor.LAN)
    assert asyncio.run(tv.handle(forged)).status is HTTPStatus.FORBIDDEN


def test_a_phone_paired_on_the_home_page_opens_the_remote_without_a_code(
    app: SlideshowApp, tmp_path: Path
) -> None:
    """A cookie `phones.json` knows opens the remote; a phone forgotten does not."""
    book = PhoneBook(tmp_path)
    token = book.add("Android")
    assert token is not None
    door = Door(_ACCESS, app.desk.screens, phones=book)
    durable = SlideshowApp(app.desk, door, app.pages, app.pictures)
    phone = _Sender(_LAN_HOST, f"{COOKIE_NAME}={token}")
    assert _ask(durable, _request("/", sender=phone)).body == _REMOTE
    assert book.forget(book.listed()[0].id)
    assert _ask(durable, _request("/", sender=phone)).status is HTTPStatus.UNAUTHORIZED


def test_the_pc_s_card_gives_the_tv_the_plain_door_under_https() -> None:
    """The slideshow's card: the TV on the plain door, the steps beside it."""
    secure = LanAccess(_PC_ADDRESS, _TV_PORT, b"cd" * 32, secure=True)
    card = json.loads(lan_response(secure, tv=True).body)
    assert card["url"].startswith("https://")
    assert card["tv"] == f"http://{_TV_HOST}/screen"
    assert card["ca"] == f"http://{_TV_HOST}{PHONE_STEPS}"
    assert "tv" not in json.loads(lan_response(_ACCESS, tv=True).body)


def test_the_slideshow_s_phone_door_is_tls_when_lan_is_mounted(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """With `/lan`, the slideshow's access is HTTPS, as the home page's."""
    monkeypatch.setenv(LAN_ADDRESS_VARIABLE, _PC_ADDRESS)
    monkeypatch.setenv("MEDIA_HYGIENE_LAN_DIR", str(tmp_path))
    access = lan_access(_TV_PORT)
    assert access is not None
    assert access.secure
    assert access.pair_url.startswith(f"https://{_LAN_HOST}/pair/")
    assert secure_door(_PC_ADDRESS) is not None
