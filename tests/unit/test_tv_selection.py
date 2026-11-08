"""0454: the files picked on a page of tiles, shown on the TV by the home server.

The page's albums API (`action: "tv"`) turns its keys into files of the index, caps
them as an album, and hands them to the home server's slideshow, which shows exactly
them in place of the show running.
"""

from __future__ import annotations

import asyncio
import contextlib
import json
from concurrent.futures import ThreadPoolExecutor
from dataclasses import dataclass
from http import HTTPStatus
from pathlib import Path
from typing import TYPE_CHECKING, Final, cast

import pytest

from media_hygiene.review.app import ReviewApp
from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.search.aside_filter import Kept
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services import slideshow_here
from media_hygiene.services.albums import album_desk
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.review_file import review_page
from media_hygiene.services.review_here import on_tv
from media_hygiene.services.slideshow_here import SlideshowHere
from media_hygiene.services.slideshow_selection import TvSlot
from media_hygiene.share.album_api import MAX_ADDED, AlbumAsked
from media_hygiene.share.album_pickers import SearchPicker
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator

    from media_hygiene.i18n.live import Page
    from media_hygiene.review.session import ReviewSession
    from media_hygiene.services.runtime import Runtime

_PHOTOS: Final = 4


@dataclass(frozen=True, slots=True)
class Served:
    """The home server's slideshow, and the slot its pages send to."""

    slideshow: SlideshowHere
    tv: TvSlot


@pytest.fixture
def here(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Iterator[Served]:
    """The home server's slideshow, listening, over an index of four photos."""
    index = tmp_path / "index.sqlite"
    indexed_photos(index, tmp_path / "photos", _PHOTOS)

    @contextlib.contextmanager
    def opened(_runtime: Runtime, *, words: bool) -> Iterator[SearchIndex]:
        assert not words
        with SearchIndex.open(index) as search:
            yield search

    monkeypatch.setattr(slideshow_here, "open_search", opened)
    runtime = make_runtime(make_locations(tmp_path))
    with ThreadPoolExecutor(1) as executor:
        server = HomeServer(None, Ending(), executor)
        built = SlideshowHere(FreshRuntime(runtime), server)
        yield Served(built, server.tv)
        built.close()


def _send(here: Served, tmp_path: Path, keys: list[str]) -> Response:
    with SearchIndex.open(tmp_path / "index.sqlite") as search:
        runtime = make_runtime(make_locations(tmp_path))
        desk = album_desk(runtime, SearchPicker(search).files, here.tv)
        body = json.dumps({"action": "tv", "album": "", "keys": keys}).encode()
        return asyncio.run(desk.answer(body))


def _shown(here: Served) -> list[int]:
    request = Request("GET", "/slideshow/api/slides", {"host": "127.0.0.1:8088"})
    answer = asyncio.run(here.slideshow.handle(request))
    return [slide["key"] for slide in json.loads(answer.body)["slides"]]


def test_the_keys_picked_start_a_show_of_exactly_them(
    here: Served, tmp_path: Path
) -> None:
    """Keys 3 and 1: a show of those two, in name order (undated); the remote."""
    answer = _send(here, tmp_path, ["3", "1"])
    assert answer.status is HTTPStatus.OK
    assert json.loads(answer.body) == {
        "page": "/slideshow/",
        "screen": "/slideshow/screen?here=1",
        "replaced": False,
    }
    assert _shown(here) == [1, 3]


def test_a_second_send_replaces_the_show_running(here: Served, tmp_path: Path) -> None:
    """The second selection is shown alone, and the answer says it replaced one."""
    _send(here, tmp_path, ["1"])
    answer = _send(here, tmp_path, ["2", "4"])
    assert json.loads(answer.body)["replaced"] is True
    assert _shown(here) == [2, 4]


def test_a_key_not_in_the_index_is_refused(here: Served, tmp_path: Path) -> None:
    """An unknown key, or a path, names nothing: nothing is shown, the reason said."""
    answer = _send(here, tmp_path, ["99", "/etc/passwd"])
    assert answer.status is HTTPStatus.CONFLICT
    assert json.loads(answer.body)["error"]
    assert here.slideshow.app is None


def test_more_files_than_an_album_takes_are_refused(tmp_path: Path) -> None:
    """3001 files: the album's message, the TV never asked."""
    asked: list[tuple[Path, ...]] = []

    def tv(files: tuple[Path, ...]) -> Response:
        asked.append(files)
        return Response(HTTPStatus.OK)

    def many(_asked: AlbumAsked) -> Kept:
        return Kept(tuple(Path(f"/data/c/{n}.jpg") for n in range(MAX_ADDED + 1)))

    desk = album_desk(make_runtime(make_locations(tmp_path)), many, tv)
    body = json.dumps({"action": "tv", "album": "", "all": True}).encode()
    answer = asyncio.run(desk.answer(body))
    assert answer.status is HTTPStatus.CONFLICT
    assert str(MAX_ADDED + 1) in json.loads(answer.body)["error"]
    assert not asked


def test_a_page_without_a_slideshow_says_where_to_open_it() -> None:
    """An empty slot (no home server): 404 and the way to the TV."""
    answer = TvSlot()(())
    assert answer.status is HTTPStatus.NOT_FOUND
    assert json.loads(answer.body)["error"]


def test_the_remote_says_once_a_selection_replaced_a_show(
    here: Served, tmp_path: Path
) -> None:
    """The first show replaced nothing; the second one tells its 2 files (0655)."""
    _send(here, tmp_path, ["1"])
    app = here.slideshow.app
    assert app is not None
    assert app.desk.state()["replaced"] == {"files": 0, "show": 0}
    _send(here, tmp_path, ["2", "4"])
    app = here.slideshow.app
    assert app is not None
    state = app.desk.state()
    assert state["replaced"] == {"files": 2, "show": state["version"]}


def test_an_album_started_from_the_home_page_tells_no_selection(
    here: Served, tmp_path: Path
) -> None:
    """Only a selection sent from a page is told: a show replaced by a pick of files."""
    _send(here, tmp_path, ["1"])
    app = here.slideshow.app
    assert app is not None
    assert app.desk.replaced == (0, 0)


def test_the_burst_review_offers_the_tv_and_its_albums_show_there() -> None:
    """📺 in the burst review's bar (hidden until a TV is paired), not in the others."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    page = review_page("review.html.j2", place, ("/decide", "/file")).decode()
    assert 'id="tvSend"' in page
    assert 'data-paired="/api/tv-paired"' in page
    other = review_page("unwanted_review.html.j2", place, ("/decide", "/file"))
    assert b'id="tvSend"' not in other


def test_on_tv_gives_the_slot_to_a_review_with_albums(tmp_path: Path) -> None:
    """The home server's slot reaches the review's albums; others are left as is."""
    runtime = make_runtime(make_locations(tmp_path))
    albums = album_desk(runtime, lambda _asked: Kept(()))
    session = cast("ReviewSession", object())
    page = cast("Page", object())
    with ThreadPoolExecutor(1) as executor:
        app = ReviewApp(session, page, executor, None, albums)
        slot = TvSlot()
        given = on_tv(app, slot)
        assert isinstance(given, ReviewApp)
        assert given.albums is not None
        assert given.albums.tv is slot
        bare = ReviewApp(session, page, executor)
        assert on_tv(bare, slot) is bare
