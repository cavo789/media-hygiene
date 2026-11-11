"""Guest devices see the albums chosen for guests only (0684).

A table over every route the home network's doors know: a guest's device gets 404 on
each, but its albums' own; its requests never reach the home page behind. The
guests' code pairs a guest (this run, or for good under HTTPS, `role = "guest"`); the
slideshow's door never takes a guest for a phone; an album taken off the guests' list
is gone at the next request.
"""

from __future__ import annotations

import asyncio
import json
from contextlib import contextmanager
from datetime import UTC, datetime
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, cast, override

import pytest

from media_hygiene.review.doors import Door
from media_hygiene.review.ending import Ending, EndingDoor
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.http import ContentType, Request, Response
from media_hygiene.review.lan import COOKIE_NAME, PAIR_PREFIX, LanAccess
from media_hygiene.review.lan_app import LanApp
from media_hygiene.review.lan_card import lan_response
from media_hygiene.review.lan_guest import code_role, guest_code, guest_token
from media_hygiene.review.lan_paths import (
    LAN_PATH,
    POST_PATHS,
    READ_PATHS,
    READ_PREFIXES,
)
from media_hygiene.review.lan_phone_model import FAMILY, GUEST, Phone, Phones
from media_hygiene.review.lan_phones import PhoneBook
from media_hygiene.review.lan_phones_api import PHONE_PATHS
from media_hygiene.review.local_app import LocalApp
from media_hygiene.review.write_routes import CHANGES
from media_hygiene.search.views import ORIGINAL_PREFIX
from media_hygiene.share.album_guest_door import AlbumGuestDoor
from media_hygiene.share.album_link_door import ALBUM_LINK_PATH
from media_hygiene.slideshow.door import Door as ShowDoor
from media_hygiene.slideshow.door import Visitor

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.share.album_shelf import Keyed
    from media_hygiene.slideshow.pictures import ShowPictures
    from media_hygiene.slideshow.screens import Screens

_PORT: Final = 8765
_HOST: Final = f"192.168.1.20:{_PORT}"
_ACCESS: Final = LanAccess("192.168.1.20", _PORT, b"cd" * 32)
_GUEST_PAGE: Final = b"<html data-guest>"
_STOP: Final = "/api/stop"
# The guests' routes, each with what it answers for the album "Crete" (ticked).
_ALLOWED: Final = {
    "/": HTTPStatus.SEE_OTHER,
    "/albums": HTTPStatus.OK,
    "/api/album-list": HTTPStatus.OK,
    "/api/album/Crete": HTTPStatus.OK,
    "/api/album/crete": HTTPStatus.OK,
    "/thumb/1.jpg": HTTPStatus.OK,
    "/tv/1.jpg": HTTPStatus.OK,
    "/film/1.mp4": HTTPStatus.OK,
}


class _Home(LocalApp):
    """Stands for the home page: answers every request, keeps its path."""

    __slots__ = ("seen",)

    def __init__(self) -> None:
        """Start without any request."""
        self.seen: list[str] = []

    @override
    async def answer(self, request: Request) -> Response:
        """Keep the path, answer a page."""
        self.seen.append(request.path)
        return Response(HTTPStatus.OK, b"<html >family", ContentType.HTML)


class _Pictures:
    """Serves a picture whose key the album allows."""

    def __init__(self, keys: frozenset[int]) -> None:
        """Keep the keys allowed."""
        self.keys = keys

    async def answer(self, request: Request) -> Response | None:
        """200 for an allowed key, 404 for another."""
        key = int(request.path.rsplit("/", 1)[1].split(".")[0])
        ok = key in self.keys
        return Response(HTTPStatus.OK if ok else HTTPStatus.NOT_FOUND, b"img")


class _Shelf:
    """Two albums: "Crete" (key 1), "Private" (key 2); `ticked` shown to guests."""

    def __init__(self) -> None:
        """Crete ticked for guests, Private not."""
        self.ticked = {"Crete"}
        self.asked: list[frozenset[int]] = []

    def _view(self, name: str) -> dict[str, object]:
        """One album's view."""
        return {"name": name, "guests": name in self.ticked}

    def listing(self) -> Keyed:
        """Both albums."""
        albums = [self._view("Crete"), self._view("Private")]
        return {"albums": albums}, frozenset({1, 2})

    def album(self, name: str) -> Keyed | None:
        """One album by name, any case."""
        found = {"crete": ("Crete", 1), "private": ("Private", 2)}.get(name.lower())
        return None if found is None else (self._view(found[0]), frozenset({found[1]}))

    @contextmanager
    def pictures(self, keys: frozenset[int]) -> Iterator[ShowPictures]:
        """Pictures of these keys only."""
        self.asked.append(keys)
        yield cast("ShowPictures", _Pictures(keys))


def _app(phones: PhoneBook | None = None) -> tuple[LanApp, _Home, _Shelf]:
    home, shelf = _Home(), _Shelf()
    door = AlbumGuestDoor(shelf, _GUEST_PAGE)
    return (
        LanApp(home, _ACCESS, b"<p>phone</p>", phones=phones, guests=door),
        home,
        shelf,
    )


def _ask(app: LanApp, path: str, how: tuple[str, str] = ("GET", "")) -> Response:
    method, token = how
    headers = {
        "host": _HOST,
        "cookie": f"{COOKIE_NAME}={token or guest_token(_ACCESS)}",
    }
    if method != "GET":
        headers |= {"content-type": "application/json", "origin": _ACCESS.origin}
    request = Request(method, path, headers, b"{}", Door.LAN)
    return asyncio.run(EndingDoor(app, Ending()).handle(request))


def _every_route() -> list[str]:
    """Every path the home network's doors know, a prefix with a file under it."""
    prefixed = [f"{prefix}2.jpg" for prefix in READ_PREFIXES]  # 2: Private's
    known = {*READ_PATHS, *POST_PATHS, *CHANGES, *PHONE_PATHS, *prefixed}
    known |= {LAN_PATH, ALBUM_LINK_PATH, f"{ORIGINAL_PREFIX}1.jpg"}
    known |= {f"{REPORTS_PREFIX}.mh-step.json", f"{REPORTS_PREFIX}index.html"}
    known |= {"/api/step", "/api/audit", "/api/stop", "/docs/", "/api/album/Private"}
    known |= {"/thumb/2.jpg", "/tv/2.jpg", "/film/2.mp4", "/a/token"}
    known |= {"/phone/", "/phone/api/state", "/phone/api/free", "/phone/api/stop"}
    return sorted(known - set(_ALLOWED))


@pytest.mark.parametrize("path", _every_route())
@pytest.mark.parametrize("method", ["GET", "POST"])
def test_a_guest_gets_404_on_every_route_but_its_albums(path: str, method: str) -> None:
    """0684: whatever the path, nothing but the guests' albums; nothing passes on."""
    app, home, _shelf = _app()
    reply = _ask(app, path, (method, ""))
    # `/api/stop` is refused before any door: the server's own loopback guard (403)
    refused = HTTPStatus.FORBIDDEN if path == _STOP else HTTPStatus.NOT_FOUND
    assert reply.status == refused, path
    assert not home.seen


@pytest.mark.parametrize("path", sorted(_ALLOWED))
def test_a_guest_sees_its_albums(path: str) -> None:
    """0684: the page, the ticked album, its files; any `POST` of them 404."""
    app, home, _shelf = _app()
    assert _ask(app, path).status == _ALLOWED[path]
    assert _ask(app, path, ("POST", "")).status == HTTPStatus.NOT_FOUND
    assert not home.seen


def test_the_guest_home_leads_to_the_albums_and_lists_the_ticked_ones() -> None:
    """0684: `/` → `/albums`, the guest page; the list holds Crete only."""
    app, _home, _shelf = _app()
    assert any("/albums" in line for line in _ask(app, "/").headers)
    assert _ask(app, "/albums").body == _GUEST_PAGE
    listed = json.loads(_ask(app, "/api/album-list").body)
    assert [album["name"] for album in listed["albums"]] == ["Crete"]


def test_an_album_taken_off_the_guests_list_is_gone_at_the_next_request() -> None:
    """0684: the list is read on each request."""
    app, _home, shelf = _app()
    assert _ask(app, "/api/album/Crete").status == HTTPStatus.OK
    shelf.ticked.clear()
    assert _ask(app, "/api/album/Crete").status == HTTPStatus.NOT_FOUND
    assert _ask(app, "/thumb/1.jpg").status == HTTPStatus.NOT_FOUND
    assert json.loads(_ask(app, "/api/album-list").body) == {"albums": []}


def test_the_family_cookie_still_reads_everything() -> None:
    """0684: a family phone is as before: the reports pass on."""
    app, home, _shelf = _app()
    path = f"{REPORTS_PREFIX}index.html"
    assert _ask(app, path, ("GET", _ACCESS.token)).status == HTTPStatus.OK
    assert home.seen == [path]


def test_two_codes_two_roles() -> None:
    """0684: the family's and the guests' codes differ; a wrong one pairs none."""
    assert guest_code(_ACCESS) != _ACCESS.code
    assert code_role(_ACCESS, _ACCESS.code) == FAMILY
    assert code_role(_ACCESS, guest_code(_ACCESS)) == GUEST
    assert code_role(_ACCESS, "00000000") is None
    card = json.loads(lan_response(_ACCESS).body)
    assert card["guest"]["code"].replace(" ", "") == guest_code(_ACCESS)
    assert "guest" not in json.loads(lan_response(_ACCESS, tv=True).body)


def _pair(app: LanApp, code: str) -> Response:
    request = Request("GET", f"{PAIR_PREFIX}{code}", {"host": _HOST}, b"", Door.LAN)
    return asyncio.run(app.handle(request))


def _cookie(reply: Response) -> str:
    line = next(h for h in reply.headers if h.startswith("Set-Cookie"))
    return line.split(f"{COOKIE_NAME}=", 1)[1].split(";", 1)[0]


def test_the_guests_code_pairs_a_guest_for_this_run() -> None:
    """0684: plain HTTP: the run's guest token, never the family's."""
    app, _home, _shelf = _app()
    reply = _pair(app, guest_code(_ACCESS))
    assert reply.status == HTTPStatus.SEE_OTHER
    assert _cookie(reply) == guest_token(_ACCESS) != _ACCESS.token
    assert _cookie(_pair(app, _ACCESS.code)) == _ACCESS.token


def test_a_guest_paired_for_good_is_kept_as_a_guest(tmp_path: Path) -> None:
    """0684: under HTTPS, `phones.json` keeps the guest's role; its cookie is one."""
    book = PhoneBook(tmp_path)
    app, home, _shelf = _app(book)
    token = _cookie(_pair(app, guest_code(_ACCESS)))
    assert [phone.role for phone in book.listed()] == [GUEST]
    assert _ask(app, f"{REPORTS_PREFIX}index.html", ("GET", token)).status == 404
    assert _ask(app, "/api/album/Crete", ("GET", token)).status == HTTPStatus.OK
    assert not home.seen
    family = _cookie(_pair(app, _ACCESS.code))
    assert [phone.role for phone in book.listed()] == [GUEST, FAMILY]
    assert _ask(app, "/api/state", ("GET", family)).status == HTTPStatus.OK


def test_an_old_phones_file_is_family() -> None:
    """0684: a device paired before the roles keeps the whole library."""
    old = '{"phones": [{"id": "a", "name": "P", "paired": "2026-01-01T00:00:00Z", '
    old += '"digest": "d"}]}'
    assert Phones.model_validate_json(old).phones[0].role == FAMILY


class _NoScreens:
    """No TV paired."""

    def is_paired(self, token: str) -> bool:
        """None is."""
        del token
        return False


def test_the_slideshow_door_never_takes_a_guest_for_a_phone(tmp_path: Path) -> None:
    """0684: the remote and its pairing stay the family's."""
    book = PhoneBook(tmp_path)
    paired = datetime.now(UTC)
    book.save((Phone(id="g", name="T", paired=paired, digest="x", role=GUEST),))
    guest = book.guests()
    token = guest.add("Tablet") or ""
    door = ShowDoor(_ACCESS, cast("Screens", _NoScreens()), phones=book)
    headers = {"host": _HOST, "cookie": f"{COOKIE_NAME}={token}"}
    assert door.visitor(Request("GET", "/", headers)) is Visitor.STRANGER
    run = {"host": _HOST, "cookie": f"{COOKIE_NAME}={guest_token(_ACCESS)}"}
    assert door.visitor(Request("GET", "/", run)) is Visitor.STRANGER
    code = Request("GET", f"{PAIR_PREFIX}{guest_code(_ACCESS)}", {"host": _HOST})
    assert door.pair_phone(code).status == HTTPStatus.FORBIDDEN
