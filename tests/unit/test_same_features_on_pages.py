"""Pages of the same kind offer the same features, from the same parts (2026-11-12).

The maintainer's rule: a feature found on one page must be on every page that does
almost the same thing. It was broken twice in one day: S/M/L/XL tiles on `/person`
while `/library` kept its own S/M/L; 👤 *Identify someone* in one large view and not
in another. So a feature of a page of tiles or of a large view lives in a shared
template (`review/templates/`), and this test renders every page built on the frame:
each page showing photos large shows them with the same view, the same keys, the same
names line; each page of tiles sizes them with the same switch. A page that cannot
have one names its reason below.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from tests.support.page_render import FRAME_EXTENDS, render_page

_SRC: Final = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"


def _framed() -> list[str]:
    """Every page built on the frame."""
    return sorted(
        path.name
        for path in _SRC.glob("*/templates/*.html.j2")
        if path.read_text("utf-8").startswith(FRAME_EXTENDS)
    )


_PAGES: Final = {name: render_page(name) for name in _framed()}
# A page that shows photos large in a view of its own, with its reason (waiting for a
# decision).
_OWN_VIEW: Final = {
    "places.html.j2": (
        "the photo in the drawer beside the map, its spot pinned on it: the shared "
        "view covers the map (question to the maintainer, 2026-11-12)"
    ),
}
# The pages that show photos large: the shared large view (`pick_viewer.html.j2`).
_LARGE: Final = sorted(
    name
    for name, page in _PAGES.items()
    if 'id="viewer"' in page and name not in _OWN_VIEW
)
# A grid that is not tiles to size, with its reason.
_FIXED_GRIDS: Final = {
    "#compare .grid": "review's 100 % comparison (C): the screen, two or three photos",
}

# What every large view offers: its keys listed under `?`, the 👤 link, who is on the
# photo and the line to name a face there (`pick_who.js.j2`).
_VIEWER_KEYS: Final = ("←", "→", "Home", "End", "F", "I", "?", "Esc")
_VIEWER_PARTS: Final = (
    'id="personLink"',
    'id="originalLink"',
    'id="viewerWho"',
    'id="viewerWhoName"',
    "function whoNamer(",
    "function showWho(",
)


def test_the_pages_with_a_large_view_are_found() -> None:
    """The library, /person, the people page, the reviews, the phone, the albums."""
    for name in ("search.html.j2", "person.html.j2", "people.html.j2"):
        assert name in _LARGE
    assert len(_LARGE) >= 12


@pytest.mark.parametrize("template", _LARGE)
def test_every_large_view_is_the_shared_one(template: str) -> None:
    """Same markup once, same keys, 👤, who is on it, a face named right there."""
    page = _PAGES[template]
    assert page.count('id="viewer"') == 1
    for part in _VIEWER_PARTS:
        assert page.count(part) == 1, part
    help_list = page.split('id="viewerHelp"')[1].split("</dl>")[0]
    shown = re.findall(r"<kbd>([^<]+)</kbd>", help_list)
    for key in _VIEWER_KEYS:
        assert key in shown, key


@pytest.mark.parametrize("template", _LARGE)
def test_every_page_of_photos_sizes_its_tiles_with_the_shared_view(
    template: str,
) -> None:
    """S/M/L/XL and *Hide the panel*: one markup in the bar, one script, once each."""
    page = _PAGES[template]
    top = page.split('<header id="bar">')[1].split("</header>")[0]
    assert top.count('id="sizes"') == 1
    assert re.findall(r'data-size="(\w+)" title=', top) == ["s", "m", "l", "xl"]
    assert top.count('id="sideToggle"') == 1
    assert page.count('"mh-view:" + location.pathname') == 1  # tile_view.js.j2
    assert page.count('body[data-tile-size="xl"] { --tile-scale') == 1


@pytest.mark.parametrize("template", sorted(_PAGES))
def test_no_page_keeps_a_switch_or_a_view_of_its_own(template: str) -> None:
    """No second size switch (the library's S/M/L), no second large view's script."""
    page = _PAGES[template]
    assert 'data-for="size"' not in page
    assert page.count('id="sizes"') <= 1
    assert page.count("requestFullscreen(") <= 1


@pytest.mark.parametrize("template", _LARGE)
def test_every_grid_of_tiles_follows_the_size_switch(template: str) -> None:
    """A grid of tiles a fixed width would ignore S/M/L/XL: each scales by the view."""
    rules = re.findall(
        r"([^{};]+)\{[^}]*grid-template-columns: repeat\(auto-f\w+, minmax\(([^;]+)\);",
        _PAGES[template],
    )
    for selector, width in rules:
        if selector.strip() not in _FIXED_GRIDS:
            assert "--tile-scale" in width, selector


def test_the_pages_with_a_view_of_their_own_still_have_one() -> None:
    """An exemption that no longer applies is removed: the page joined the view."""
    for name in _OWN_VIEW:
        assert 'id="viewer"' in _PAGES[name]
        assert 'id="viewerWhoName"' not in _PAGES[name]
