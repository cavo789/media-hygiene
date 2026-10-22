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
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.pictures import Pictures
from media_hygiene.slideshow.app import ShowPages, SlideshowApp
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.door import Door
from media_hygiene.slideshow.pictures import ShowPictures
from media_hygiene.slideshow.screen_jpeg import ScreenJob
from media_hygiene.slideshow.screens import MAX_FAILURES, SCREEN_COOKIE, Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Slide, Timing

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
    if sender.cookie:
        headers["cookie"] = sender.cookie
    if body is None:
        return Request("GET", path, headers)
    headers |= {"content-type": _JSON, "origin": f"http://{sender.host}"}
    return Request("POST", path, headers, json.dumps(body).encode())


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
        "photo": "/tv/2.jpg",
        "film": "",
        "next": "/tv/1.jpg",
        "playing": False,
        "code": "",
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
    assert shown["photo"] == "/tv/1.jpg"
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
