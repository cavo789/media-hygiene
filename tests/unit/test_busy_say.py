"""One way to say *working*, *done* and *failed* on every page (0664).

`review/templates/busy_say.html.j2`: `mhSay` (the toast stack), `mhBusy` (a posting
button disabled, a spinner), `mhPlaceholders` (tiles while a grid loads).
Included once by the frame, the home page and the album page; no page keeps a
toast style of its own.
"""

from __future__ import annotations

from pathlib import Path
from typing import Final

import pytest

from tests.support.page_render import render_page

_TEMPLATES: Final = (
    Path(__file__).parents[2] / "src" / "media_hygiene" / "review" / "templates"
)
_SHARED: Final = (
    '<div id="mhSay" aria-live="polite">',
    "window.mhSay = ",
    "window.mhBusy = ",
    "window.mhPlaceholders = ",
)


@pytest.mark.parametrize(
    "page", ["album.html.j2", "quarantine.html.j2", "search.html.j2"]
)
def test_every_page_holds_the_three_pieces_once(page: str) -> None:
    """The frame, the home page and the album page include the shared piece once."""
    html = render_page(page)
    for part in _SHARED:
        assert html.count(part) == 1, (page, part)


def test_the_toast_takes_text_never_html() -> None:
    """A file name in a message shows as text (0671's sinks)."""
    shared = (_TEMPLATES / "busy_say.html.j2").read_text("utf-8")
    assert "innerHTML" not in shared
    assert "line.textContent = String(text);" in shared


def test_the_home_page_has_no_toast_of_its_own() -> None:
    """The home page's toasts go to the shared stack: one style, not two."""
    home = (_TEMPLATES / "home.html.j2").read_text("utf-8")
    assert home.count('{% include "busy_say.html.j2" %}') == 1
    assert 'id="toasts"' not in home
    assert ".toast-x" not in (_TEMPLATES / "home_parts.css.j2").read_text("utf-8")
    run = (_TEMPLATES / "home_run.js.j2").read_text("utf-8")
    assert "window.mhSay(message, tone);" in run


def test_posts_from_a_button_wait_busy() -> None:
    """The library's and the home page's posts keep the button busy until the answer."""
    grid = (_TEMPLATES / "pick_grid.js.j2").read_text("utf-8")
    run = (_TEMPLATES / "home_run.js.j2").read_text("utf-8")
    assert "return window.mhBusy(button, send);" in grid
    assert "window.mhBusy(document.activeElement, () => fetch(path" in run


def test_the_library_shows_placeholders_while_it_loads() -> None:
    """The first answer comes into placeholder tiles: the grid never moves."""
    search = render_page("search.html.j2")
    assert 'window.mhPlaceholders($("grid"), PLACEHOLDER_TILES);' in search
