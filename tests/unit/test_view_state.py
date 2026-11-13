"""Every page keeps its view in its URL (0666): `review/templates/view_state.html.j2`.

`mhView.get(keys)` reads only the page's known keys, each checked against its kind;
`mhView.set(values, {push})` writes them. The frame, the home page and the album page
include it once; the large view pushes a step so Back closes it.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from tests.support.page_render import render_page

_SRC: Final = Path(__file__).parents[2] / "src" / "media_hygiene"
_TEMPLATES: Final = _SRC / "review" / "templates"
_HELPER: Final = "window.mhView = Object.freeze({ get, set });"
# A hostile query string: what a link could carry into `mhView.get`.
_HOSTILE_QUERY: Final = (
    "?g=1<img src=x onerror=alert(1)>&text=</script><script>alert(1)"
)
_SINKS: Final = ("innerHTML", "insertAdjacentHTML", "outerHTML", "document.write")


@pytest.mark.parametrize(
    "page", ["album.html.j2", "quarantine.html.j2", "search.html.j2"]
)
def test_every_page_holds_the_helper_once(page: str) -> None:
    """The frame, the home page and the album page include it once, in the head."""
    html = render_page(page)
    assert html.count(_HELPER) == 1
    assert html.index(_HELPER) < html.index("</head>")


def test_the_home_page_includes_it_in_its_head() -> None:
    """The home page has no frame: its own head holds the one include."""
    home = (_TEMPLATES / "home.html.j2").read_text("utf-8")
    include = '{% include "view_state.html.j2" %}'
    assert home.count(include) == 1
    assert home.index(include) < home.index("</head>")


def test_no_page_touches_the_history_by_itself() -> None:
    """`pushState`/`replaceState` live in the helper only."""
    for path in _SRC.rglob("*.j2"):
        if path.name == "view_state.html.j2":
            continue
        text = path.read_text("utf-8")
        assert "pushState" not in text, path
        assert "replaceState" not in text, path
        # 0765: the query string is read through `mhView.get` only (each key checked).
        # The TV screen (old browsers, ES5, no frame) keeps its own test of `here=1`.
        if path.name != "screen_here.js.j2":
            assert "location.search" not in text, path


def test_values_read_from_the_url_never_become_markup() -> None:
    """Untrusted input (0671): the helper and every reader keep the values as values."""
    helper = (_TEMPLATES / "view_state.html.j2").read_text("utf-8")
    for sink in _SINKS:
        assert sink not in helper
    for path in _SRC.rglob("*.j2"):
        for line in path.read_text("utf-8").splitlines():
            if "mhView.get(" in line:
                assert not any(sink in line for sink in _SINKS), (path, line)


def test_a_hostile_query_string_fails_every_kind() -> None:
    """The kinds the helper checks: an integer or a word never holds markup."""
    helper = (_TEMPLATES / "view_state.html.j2").read_text("utf-8")
    kinds = re.search(r"int: /(.+?)/, word: /(.+?)/ ", helper)
    assert kinds is not None
    query = _HOSTILE_QUERY.lstrip("?").split("&")
    hostile = [pair.split("=", 1)[1] for pair in query]
    for pattern in kinds.groups():
        assert all(re.fullmatch(pattern, value) is None for value in hostile)


def test_the_large_view_pushes_and_back_closes_it() -> None:
    """Opening pushes a step; Esc goes back; Back (popstate) closes the view."""
    viewer = (_TEMPLATES / "pick_viewer.js.j2").read_text("utf-8")
    assert "push: true, state: { mhViewer: true }" in viewer
    assert "window.history.back(); return;" in viewer
    assert 'window.addEventListener("popstate"' in viewer


@pytest.mark.parametrize(
    "template",
    [
        "review.html.j2",
        "near_review.js.j2",
        "pairs_review.js.j2",
        "gone_review.js.j2",
        "unwanted_review.js.j2",
        "shrink.js.j2",
    ],
)
def test_each_review_keeps_its_group(template: str) -> None:
    """Bursts, near duplicates, pairs: the group shown is the `g` key, replaced."""
    text = (_TEMPLATES / template).read_text("utf-8")
    assert 'window.mhView.get({ g: "int" }).g' in text
    assert "window.mhView.set({ g: " in text
