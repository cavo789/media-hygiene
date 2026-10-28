"""0444: a paired phone starts an album saved on the PC on the TV, nothing else.

`POST /api/step` for `slideshow-album` and an album of `albums.json` goes on to the
home page as the PC's; another step, another album, an unpaired phone: refused. The
phone's page lists the albums, or says how to make one.
"""

from __future__ import annotations

import asyncio
import json
from http import HTTPStatus
from typing import Final, override

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.lan import COOKIE_NAME, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_paths import PHONE_STEPS, phone_may
from media_hygiene.review.lan_show import asked_album
from media_hygiene.review.local_app import LocalApp
from media_hygiene.services import home

_PORT: Final = 8088
_ACCESS: Final = LanAccess("192.168.1.20", _PORT, b"ef" * 32)
_LIST: Final = "/api/album-list"


class _Home(LocalApp):
    """The home page: its albums, and the steps it was asked."""

    __slots__ = ("albums", "steps")

    def __init__(self, albums: tuple[str, ...]) -> None:
        """Hold these albums."""
        self.albums = albums
        self.steps: list[bytes] = []

    @override
    async def answer(self, request: Request) -> Response:
        """The album list, or a step taken."""
        if request.path == _LIST:
            listed = {"albums": [{"name": name} for name in self.albums]}
            return Response(
                HTTPStatus.OK, json.dumps(listed).encode(), ContentType.JSON
            )
        self.steps.append(request.body)
        return Response(HTTPStatus.OK, b"{}", ContentType.JSON)


def _step(fake: _Home, body: object, *, paired: bool = True) -> Response:
    headers = {
        "host": _ACCESS.host,
        "content-type": "application/json",
        "origin": _ACCESS.origin,
    }
    if paired:
        headers["cookie"] = f"{COOKIE_NAME}={_ACCESS.token}"
    request = Request("POST", "/api/step", headers, json.dumps(body).encode(), Door.LAN)
    app = LanApp(fake, _ACCESS, b"<p>phone</p>")
    return asyncio.run(EndingDoor(app, Ending()).handle(request))


def _show(album: str) -> dict[str, object]:
    return {"name": "slideshow-album", "fields": {"album": album}}


def test_a_paired_phone_starts_an_album_saved_on_the_pc() -> None:
    """The step goes on to the home page, whatever the album name's case."""
    fake = _Home(("Crete 2023",))
    assert _step(fake, _show("crete 2023")).status is HTTPStatus.OK
    assert fake.steps == [json.dumps(_show("crete 2023")).encode()]


@pytest.mark.parametrize(
    "body",
    [
        _show("Paris"),  # not saved: no free text
        {"name": "slideshow", "fields": {"path": "C:\\Photos"}},
        {"name": "clean", "fields": {}},
        {"number": 3, "command": "mh clean"},
        {"name": "slideshow-album", "fields": {"album": "Crete 2023", "x": "1"}},
        {},
    ],
)
def test_any_other_step_or_album_is_refused(body: object) -> None:
    """Only `slideshow-album` and an album of the list: 403, home untouched."""
    fake = _Home(("Crete 2023",))
    reply = _step(fake, body)
    assert reply.status is HTTPStatus.FORBIDDEN
    assert b"on the PC" in reply.body
    assert not fake.steps


def test_an_unpaired_phone_is_refused() -> None:
    """Without the cookie, even the album's show: 403."""
    fake = _Home(("Crete 2023",))
    assert _step(fake, _show("Crete 2023"), paired=False).status is HTTPStatus.FORBIDDEN
    assert not fake.steps


def test_no_album_saved_refuses_and_the_page_says_how_to_make_one() -> None:
    """No album: nothing to start; the phone's page has the line to make one."""
    fake = _Home(())
    assert _step(fake, _show("Crete 2023")).status is HTTPStatus.FORBIDDEN
    page = home.home_page(remote=True).decode()
    assert "tvAlbums()" in page
    assert "make one on the PC" in page
    assert '"albumList": "/api/album-list"' in page


def test_the_phones_list_stays_read_only() -> None:
    """The step is never in the phone's list: only `lan_show` lets this one body by."""
    assert {"slideshow-album"} == PHONE_STEPS
    request = Request("POST", "/api/step", {}, json.dumps(_show("A")).encode())
    assert not phone_may(request)
    assert asked_album(b"not json") is None
    assert asked_album(json.dumps(_show("  ")).encode()) is None
