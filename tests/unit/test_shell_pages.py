"""Every page in the home page's frame (0493-0496): its space, its rail, its parts.

Search and browse (*Find*), the six reviews (*Clean*), people and a person (*Find*),
the places map (*Sort*), history (*History and undo*) and shrink (*Clean*): rendered as
served, they carry the sidebar, highlight their space, and their sticky parts sit under
its top bar.
"""

from __future__ import annotations

import re
from typing import Final

import pytest

from media_hygiene.review.page_header import PAGE_STEPS, SHELL_PAGES
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.page_render import render_page

_CURRENT: Final = re.compile(r'data-space="([a-z]+)" aria-current="page"')
_SPACES: Final = {
    "search.html.j2": "find",
    "review.html.j2": "clean",
    "near_review.html.j2": "clean",
    "pairs_review.html.j2": "clean",
    "gone_review.html.j2": "clean",
    "intruders_review.html.j2": "clean",
    "unwanted_review.html.j2": "clean",
    "people.html.j2": "find",
    "person.html.j2": "find",
    "places.html.j2": "sort",
    "history.html.j2": "history",
    "shrink.html.j2": "clean",
}
# What keeps the thin bar: the phone's page (read-only) and the slideshow (full screen).
_THIN: Final = {"phone_review.html.j2", "slideshow.html.j2"}


def test_every_page_but_the_phones_and_the_slideshow_is_in_the_frame() -> None:
    """0493-0496 moved them all; what stays out is named."""
    assert set(PAGE_STEPS) - set(SHELL_PAGES) == _THIN


@pytest.mark.parametrize(("template", "space"), sorted(_SPACES.items()))
def test_each_moved_page_highlights_its_space(
    template: str, space: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """From the home page: the sidebar, its space current, no thin bar."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    page = render_page(template)
    assert page.count('id="mhShellSide"') == 1
    assert 'class="mh-bar"' not in page
    assert _CURRENT.findall(page) == [space]
    folded = '"mh-shelled", "mh-shell-compact"' in page
    assert folded is SHELL_PAGES[template]


def test_the_tile_pages_and_the_map_keep_their_columns() -> None:
    """Tiles or the map: the 64 px rail; history and shrink: the full sidebar."""
    folded = {name for name, compact in SHELL_PAGES.items() if compact}
    assert {"search.html.j2", "review.html.j2", "places.html.j2"} <= folded
    assert not {"history.html.j2", "shrink.html.j2", "album.html.j2"} & folded


@pytest.mark.parametrize("template", ["review.html.j2", "people.html.j2"])
def test_sticky_parts_sit_under_the_top_bar(template: str) -> None:
    """`#bar`, `#side`, people's header: under the measured top bar."""
    page = render_page(template)
    assert "top: var(--mh-shell-top-h, 0px)" in page
    assert 'root.style.setProperty("--mh-shell-top-h"' in page
    assert "html.mh-shelled #viewer" in page  # the large view covers the sidebar


def test_the_map_keeps_leaflet_under_the_top_bar() -> None:
    """Leaflet's z-index 400-1000 stays inside `#stage`; the map fills what is left."""
    page = render_page("places.html.j2")
    assert "html.mh-shelled #stage { isolation: isolate; }" in page
    assert "#map { position: absolute; inset: 0; }" in page


def test_the_shell_uses_no_key_a_review_needs() -> None:
    """0494: the frame binds no key; the reviews keep theirs (Z, arrows, Ctrl+A...)."""
    page = render_page("review.html.j2")
    script = page.split('id="mhShellMenu"')[1].split("</script>")[0]
    assert "keydown" not in script
