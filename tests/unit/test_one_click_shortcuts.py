"""0523: an album in one click, the TV on a card, the end of a step told."""

from __future__ import annotations

import asyncio
import json
from dataclasses import replace
from http import HTTPStatus
from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Final, cast

import pytest

from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.review.lan_phones import PhoneBook
from media_hygiene.search.aside_filter import AsideFilter
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services.albums import album_desk, album_store
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.slideshow_selection import TvSlot, any_tv
from media_hygiene.share.album_page import TV_PAIRED_PATH, AlbumPages, AlbumParts
from media_hygiene.share.album_pickers import SearchPicker
from media_hygiene.slideshow.screens import Screens
from tests.support.indexed_photos import indexed_photos
from tests.support.page_render import render_page
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.share.album_api import AlbumDesk
    from media_hygiene.share.album_shelf import AlbumShelf, Shown

_PHOTOS: Final = 3
_ROOT: Final = Path(__file__).parents[2] / "src" / "media_hygiene"


def _post(tmp_path: Path, asked: dict[str, object], aside: frozenset[str]) -> Response:
    """An album request, answered over three indexed photos; `aside`: host paths."""
    index = tmp_path / "index.sqlite"
    if not index.exists():
        indexed_photos(index, tmp_path / "photos", _PHOTOS)
    (tmp_path / "reports").mkdir(exist_ok=True)
    runtime = make_runtime(make_locations(tmp_path))
    with SearchIndex.open(index) as search:
        kept = AsideFilter(lambda: aside, runtime.mapper)
        desk: AlbumDesk = album_desk(runtime, SearchPicker(search, kept).files)
        desk = _ready(desk)
        return asyncio.run(desk.answer(json.dumps(asked).encode()))


def _ready(desk: AlbumDesk) -> AlbumDesk:
    """The desk, its reports folder taken as mounted (`tmp_path`)."""
    return replace(desk, ready=lambda: None)


def _on_disk(tmp_path: Path) -> dict[str, int]:
    """Each album and how many files it holds, read back from the file."""
    store = album_store(make_runtime(make_locations(tmp_path)))
    return {each.name: len(each.entries) for each in store.on_disk().albums.albums}


def test_an_album_of_an_events_files_is_read_back_from_the_disk(tmp_path: Path) -> None:
    """The card sends the event's keys under its name: on disk, said in the answer."""
    keys = ["1", "2"]
    answer = _post(
        tmp_path, {"action": "add", "album": "Crete", "keys": keys}, frozenset()
    )
    assert answer.status is HTTPStatus.OK
    said = json.loads(answer.body)
    assert [each["name"] for each in said["albums"]] == ["Crete"]
    assert _on_disk(tmp_path) == {"Crete": 2}


def test_an_album_of_a_search_takes_every_file_found_but_those_set_aside(
    tmp_path: Path,
) -> None:
    """`all`: the three found; the second run with one set aside leaves it out."""
    asked = {"action": "add", "album": "All", "all": True, "search": {}}
    assert _post(tmp_path, asked, frozenset()).status is HTTPStatus.OK
    assert _on_disk(tmp_path) == {"All": _PHOTOS}
    runtime = make_runtime(make_locations(tmp_path))
    aside = runtime.mapper.to_host(min((tmp_path / "photos").iterdir()))
    other = {**asked, "album": "Kept"}
    answer = _post(tmp_path, other, frozenset({aside}))
    assert _on_disk(tmp_path)["Kept"] == _PHOTOS - 1
    assert "1" in json.loads(answer.body)["message"]


def test_every_file_set_aside_makes_no_album(tmp_path: Path) -> None:
    """Nothing to put in it: the answer lists no such album, the page says why."""
    _post(tmp_path, {"action": "add", "album": "First", "keys": ["1"]}, frozenset())
    runtime = make_runtime(make_locations(tmp_path))
    every = frozenset(
        runtime.mapper.to_host(photo) for photo in (tmp_path / "photos").iterdir()
    )
    asked: dict[str, object] = {"action": "add", "album": "Empty", "keys": ["1", "2"]}
    answer = _post(tmp_path, asked, every)
    names = [each["name"] for each in json.loads(answer.body).get("albums", [])]
    assert "Empty" not in names
    assert "Empty" not in _on_disk(tmp_path)


def test_no_slideshow_listening_means_no_tv() -> None:
    """The slot says False until the slideshow fills it."""
    slot = TvSlot()
    assert slot.paired() is False
    slot.known = lambda: True
    assert slot.paired() is True


def test_a_tv_kept_for_good_counts_before_its_next_visit(tmp_path: Path) -> None:
    """`tvs.json` holds one: paired, though no TV came this run; else not."""
    phones = PhoneBook(tmp_path, "phones.json")
    screens = Screens(phones.tvs())
    assert any_tv(screens, None) is False
    assert any_tv(screens, phones) is False
    phones.tvs().keep("token", "TV")
    assert any_tv(screens, phones) is True


@pytest.mark.parametrize("paired", [True, False])
def test_the_pages_ask_whether_a_tv_is_paired(paired: bool) -> None:  # noqa: FBT001
    """`GET /api/tv-paired` answers what the slot knows."""
    server = HomeServer(None, Ending(), cast("object", None))  # type: ignore[arg-type]
    server.tv.known = lambda: paired
    parts = AlbumParts(
        b"",
        cast("AlbumShelf", None),
        cast("AlbumDesk", None),
        cast("Shown", None),
        tv_paired=server.tv.paired,
    )
    pages = AlbumPages(cast("Handling", SimpleNamespace()), parts)
    request = Request("GET", TV_PAIRED_PATH, {"host": "127.0.0.1:8088"})
    answer = asyncio.run(pages.handle(request))
    assert json.loads(answer.body) == {"paired": paired}


def test_the_event_card_offers_the_album_and_hides_the_tv() -> None:
    """📚 always, 📺 hidden until a TV is known; the search's button hidden at first."""
    page = render_page("search.html.j2")
    assert 'id="spanAlbum"' in page
    assert 'id="spanTv" class="plain" hidden' in page
    assert (
        'id="albumResults" class="plain writes" role="menuitem" type="button" hidden'
        in page
    )
    assert "offerAlbum(body, narrowed ? 0 : found.total)" in page  # never over a filter


def test_the_bar_s_tv_is_greyed_until_a_tv_is_paired() -> None:
    """▶ Slideshow ▾ (0660): 📺 On the TV greyed, with its *how*, until `paired`."""
    page = render_page("search.html.j2")  # every route named: "/x"
    assert 'id="showBar"' in page
    assert 'data-paired="/x"' in page
    assert '$("showTv").disabled = !yes || n === 0; $("showHow").hidden = yes;' in page
    assert 'id="tvSend"' not in page


def test_without_the_home_server_no_tv_and_no_album_tab() -> None:
    """`mh library` alone: no 📺 (`tv_here`), and the album is only said, not opened."""
    card = (_ROOT / "search/templates/search_events.html.j2").read_text("utf-8")
    assert '{% if tv_here | default(false) %}<button type="button" id="spanTv"' in card
    script = (_ROOT / "search/templates/search_shortcuts.js.j2").read_text("utf-8")
    assert '("/albums/edit" if tv_here | default(false) else "")' in script


def test_the_albums_card_starts_the_albums_show_only_with_a_tv() -> None:
    """The link is drawn when the page was told a TV is paired, on the PC."""
    script = (_ROOT / "share/templates/album.js.j2").read_text("utf-8")
    assert 'hasAttribute("data-phone")) return false' in script
    assert '${paired ? `<a class="totv pc-only"' in script
    assert "P.tv_album + encodeURIComponent(each.name)" in script


def test_the_end_of_a_step_notifies_only_a_tab_away_and_asks_once() -> None:
    """Asked in the click, the answer kept; the toast is enough for a tab in front."""
    notify = (_ROOT / "review/templates/step_chip.html.j2").read_text("utf-8")
    run = (_ROOT / "review/templates/home_run.js.j2").read_text("utf-8")
    assert "|| kept()) return;" in notify
    assert "Notification.requestPermission().then(keep)" in notify
    assert "if (!document.hidden" in notify
    assert 'if (action.kind !== "page") notifyAsk();' in run
    assert "notifyEnd(ended);" in run


def test_the_album_of_the_found_sits_in_the_album_menu() -> None:
    """0695: *Album of the N found* is in 📚 Album ▾, stating its count."""
    page = render_page("search.html.j2")
    menu = page[
        page.index('id="albumBar"') : page.index(
            "</details>", page.index('id="albumBar"')
        )
    ]
    assert 'id="albumResults"' in menu
    assert page.count('id="albumResults"') == 1
    assert "albumResultsLine" not in page
    assert "Album of the {n} found" in page
    # the count stated: the same total as *Pick all N found*
    assert "button.textContent = counted(TEXTS.albumResults, found);" in page
