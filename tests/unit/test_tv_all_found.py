"""0833: nothing picked, ▶ Slideshow sends every file found, not the first shown."""

from __future__ import annotations

import asyncio
import contextlib
import json
from concurrent.futures import ThreadPoolExecutor
from importlib.resources import files
from typing import TYPE_CHECKING, Final

from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request
from media_hygiene.search.fts import SearchIndex
from media_hygiene.search.views import FIRST_HITS
from media_hygiene.services import slideshow_here
from media_hygiene.services.albums import album_desk
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.slideshow_here import SlideshowHere
from media_hygiene.share.album_pickers import SearchPicker
from tests.support.indexed_photos import indexed_photos
from tests.support.runtime import make_locations, make_runtime

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    import pytest

    from media_hygiene.services.runtime import Runtime

_FOUND: Final = FIRST_HITS + 60


def test_every_file_found_reaches_the_show(
    tmp_path: Path, monkeypatch: pytest.MonkeyPatch
) -> None:
    """300 found, 240 shown, nothing picked: the show holds the 300."""
    index = tmp_path / "index.sqlite"
    indexed_photos(index, tmp_path / "photos", _FOUND)

    @contextlib.contextmanager
    def opened(_runtime: Runtime, *, words: bool) -> Iterator[SearchIndex]:
        assert not words
        with SearchIndex.open(index) as search:
            yield search

    monkeypatch.setattr(slideshow_here, "open_search", opened)
    runtime = make_runtime(make_locations(tmp_path))
    shown = [str(key) for key in range(1, FIRST_HITS + 1)]
    body = {"action": "tv", "album": "", "keys": shown, "all": True, "search": {}}
    with ThreadPoolExecutor(1) as executor, SearchIndex.open(index) as search:
        server = HomeServer(None, Ending(), executor)
        built = SlideshowHere(FreshRuntime(runtime), server)
        desk = album_desk(runtime, SearchPicker(search).files, server.tv)
        answer = asyncio.run(desk.answer(json.dumps(body).encode()))
        request = Request("GET", "/slideshow/api/slides", {"host": "127.0.0.1:8088"})
        slides = json.loads(asyncio.run(built.handle(request)).body)["slides"]
        built.close()
    assert json.loads(answer.body)["page"] == "/slideshow/"
    assert len(slides) == _FOUND


def _template(name: str) -> str:
    return (files("media_hygiene.review") / "templates" / name).read_text("utf-8")


def test_the_menu_counts_what_the_show_is_sent() -> None:
    """One `showing()`: the menu's count and the files sent never differ (0833, 0837).

    What is picked is what is sent, like every other button: every file shown
    picked (Ctrl+A) is those shown; nothing picked on a partial search is every
    file found (`all`, counted as `total`), and the menu says so.
    """
    grid = _template("pick_grid.js.j2")
    assert "if (everything) return { keys: [], all: true, count: total };" in grid
    assert "allShown" not in grid.split("function showing()")[1].split("}")[0]
    nothing = "if (total > files.length) return { keys: [], all: true, count: total };"
    assert nothing in grid
    assert grid.index("picked.size > 0) return") < grid.index(nothing)
    assert "const { keys, all } = showing();" in grid
    menu = _template("slideshow_menu.html.j2")
    assert 'id="showNone"' in menu
    assert "data-every=" in menu
    script = _template("pick_slideshow.js.j2")
    assert "const { count: n, all } = showing();" in script
    assert "menu.dataset.every" in script


def test_picking_every_file_shown_offers_every_file_found() -> None:
    """Ctrl+A on 240 of 344: a toast with *Pick all 344*, which picks them (0837).

    Only on a partial search (`total > files.length`), once per such picking,
    through the frame's shared `mhSay` with its action button.
    """
    grid = _template("pick_grid.js.j2")
    body = grid.split("function offerAll()")[1].split("\n}\n")[0]
    assert "total > files.length" in body
    assert "!allShownSaid" in body
    assert "window.mhSay(" in body
    assert "everything = true; showPicked();" in body
    assert "offerAll();" in grid.split("function showPicked()")[1]
    say = _template("busy_say.html.j2")
    assert 'window.mhSay = (text, tone = "info", action = null) =>' in say
    assert "action.run();" in say
    search = files("media_hygiene.search") / "templates" / "search.html.j2"
    assert '"partialPick":' in search.read_text("utf-8")
