"""One frame for every page served (0333): the same parts, at the same place, once each.

`review/templates/page_frame.html.j2`: the bar on top and the way home, the left column
(`#side`) with the ⌨ panel (`#keys`) when the page has keys, one bar on top of the
right column (`#bar`), no second header, no footer. A page that differs is named below
with the reason it differs; a temporary one names what it waits for.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.review.page_header import PAGE_STEPS
from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.page_render import FRAME_EXTENDS, render_page

_SRC: Final = Path(__file__).resolve().parents[2] / "src" / "media_hygiene"
_FRAME: Final = "page_frame.html.j2"

# The pages left off the frame, each with its reason.
EXEMPT: Final = {
    "home.html.j2": "the home page itself: its own shell, the standard of its own",
    "doc.html.j2": "the documentation, shown in the home page's shell",
    "lan_pair.html.j2": "a phone not paired yet: nothing to go back to (0269)",
    "screen.html.j2": "the TV: a 2012 browser, a black screen, no UI",
    "base.html.j2": "an HTML report opened from the disk: no server, no way home",
    "album.html.j2": (
        "served in front of the home page by its own server: its ⌂ link goes back "
        "without ending a server; laid out for a phone (a tap, a swipe)"
    ),
    "people.html.j2": "temporary: until 0323-0329 are done (they reshape this page)",
}


def _pages() -> dict[str, str]:
    """Every template that is a whole page: its name and its source."""
    found = {}
    for path in sorted(_SRC.glob("*/templates/*.html.j2")):
        text = path.read_text("utf-8")
        whole = text.startswith(("<!DOCTYPE", FRAME_EXTENDS))
        if whole and path.name != _FRAME:
            found[path.name] = text
    return found


_FRAMED: Final = sorted(set(_pages()) - set(EXEMPT))


def test_every_page_is_framed_or_says_why_not() -> None:
    """A new page is on the frame, or added to the exemptions with its reason."""
    pages = _pages()
    assert set(EXEMPT) <= set(pages)
    for name in _FRAMED:
        assert pages[name].startswith(FRAME_EXTENDS), name
        assert name in PAGE_STEPS, name  # served, with its chapter of the docs
    assert len(_FRAMED) >= 11


@pytest.fixture(autouse=True)
def _from_home(monkeypatch: pytest.MonkeyPatch) -> None:
    """`mh` opened the pages from the home page: the way back shows."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")


@pytest.mark.parametrize("template", _FRAMED)
def test_each_framed_page_holds_the_parts_once(template: str) -> None:
    """The bar and the way home, `#side`, `#bar`; nothing else above the content."""
    page = render_page(template)
    assert page.count('class="mh-bar"') == 1
    assert page.count('id="homeLink"') == 1
    assert page.count('id="homeClosed"') == 1  # home_link.html.j2
    assert page.count('<aside id="side">') == 1
    assert page.count('<header id="bar">') == 1
    assert len(re.findall(r"<header\b", page)) == 1  # no second header
    assert "<footer" not in page
    assert page.count("<!DOCTYPE html>") == 1
    content = page.split('<div id="content">')[1]
    assert content.index('<header id="bar">') < content.index("<main")


@pytest.mark.parametrize("template", _FRAMED)
def test_a_page_with_keys_shows_them_at_the_bottom_of_the_left_column(
    template: str,
) -> None:
    """`keydown` handled: the ⌨ panel, once, last in `#side`; none without keys."""
    page = render_page(template)
    has_keys = '"keydown"' in page
    assert page.count('id="keys"') == int(has_keys), template
    if has_keys:
        side = page.split('<aside id="side">')[1].split("</aside>")[0]
        assert side.rstrip().endswith("</section>")
        assert side.index('id="keys"') > side.find('id="toc"')
        assert "<kbd>" in side.split('id="keys"')[1]


# A key each page shows in sight (0304): the panel is the page's own.
_MAIN_KEY: Final = {
    "review.html.j2": "only the sharpest, then next",
    "near_review.html.j2": "keep the other version, then next",
    "gone_review.html.j2": "deleted on purpose: remembered",
    "unwanted_review.html.j2": "the group as marked, then next",
    "pairs_review.html.j2": "swap the folders, then next",
    "sort_review.html.j2": "accept the name and category",
    "places.html.j2": "close the large photo, then the photos of the place",
    "browse.html.j2": "every file from the last one clicked",
    "search.html.j2": "every file from the last one clicked",
    "phone_review.html.j2": "every file from the last one clicked",
}


@pytest.mark.parametrize(("template", "key"), sorted(_MAIN_KEY.items()))
def test_each_page_shows_its_main_keys_in_the_panel(template: str, key: str) -> None:
    """In sight, before *More keys*; the old line of keys under the content is gone."""
    page = render_page(template)
    panel = page.split('id="keys"')[1].split("</section>")[0]
    assert key in panel.split('id="moreKeys"')[0]
    assert '<p class="safe">🔒 ' in panel
    assert "Ctrl+C in the terminal" not in page.split("</aside>")[1].split("<script")[0]


def test_review_sort_keeps_its_fields_in_the_bar_and_the_event_on_the_left() -> None:
    """The name and category where the eye is, the facts of the event on the left."""
    page = render_page("sort_review.html.j2")
    top = page.split('<header id="bar">')[1].split("</header>")[0]
    assert 'id="choice"' in top
    assert 'id="name"' in top
    side = page.split('<aside id="side">')[1].split("</aside>")[0]
    assert 'id="facts"' in side
    assert "<kbd>Space</kbd>" not in page  # the line of twelve keys under the photos
