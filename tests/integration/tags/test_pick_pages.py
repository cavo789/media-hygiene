"""`search`, `browse`, the reviews: one page of photos to pick, same keys and bar."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services.review_file import review_page
from tests.support.pick_pages import PICK_PARTS
from tests.support.search_page import serve_search

if TYPE_CHECKING:
    from typer.testing import CliRunner


# The shared parts, as each one shows in the page served (review/templates/pick_*).
_SHARED = (
    *PICK_PARTS,
    "#bar #albumBar { flex-basis: 100%",  # pick_grid.css.j2: the bar keeps its height
    '<select id="order">',  # pick_order.html.j2: Sort by (0347)
    '<select id="kind">',  # and Show
)


def _pages(cli: CliRunner, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    """The search page and the folder view, as served."""
    answers = serve_search(
        cli, monkeypatch, [("GET /search", None), ("GET /browse", None)]
    )
    return answers[0].body.decode(), answers[1].body.decode()


def test_both_pages_are_built_from_the_same_parts(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Each shared part once in each page: no copy left behind."""
    for page in _pages(cli, monkeypatch):
        for part in _SHARED:
            assert page.count(part) == 1, part
        assert page.count('"use strict";') == 1


def test_the_search_keeps_its_field_on_the_left_and_one_bar_above(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The form, the folders under it, the keys below; the bar holds the picking.

    0408: one page, no tabs; `/browse` is the same page, its folders open.
    """
    search, browse = _pages(cli, monkeypatch)
    assert browse == search
    side = search.split('<aside id="side">')[1].split("</aside>")[0]
    assert 'id="views"' not in side
    assert (
        side.index('id="form"') < side.index('id="folders"') < side.index('id="keys"')
    )
    keys = side.split('id="keys"')[1].split("</section>")[0]
    assert "every file shown" in keys  # Ctrl+A
    assert "<kbd>/</kbd>" in keys
    top = search.split('<header id="bar">')[1].split("</header>")[0]
    assert 'id="pickAll"' in top  # every file found, past those shown
    assert 'id="invert"' in top
    assert 'id="albumBar"' in top
    assert "<header>" not in search  # the seven-line header is gone


def test_a_search_sent_hands_the_keys_to_the_grid(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """After Enter in the field, Ctrl+A picks the files instead of the field's text."""
    search, _browse = _pages(cli, monkeypatch)
    sent = search.split("async function search(event, again) {")[1].split("\n}\n")[0]
    assert "document.activeElement.blur()" in sent
    assert "showFiles(found.hits, again)" in sent  # a save keeps the cards
    assert "function scope() {\n  return asked;" in search


def test_the_events_view_is_part_of_the_search_page(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0438: review-sort's choices in the search's Events view, the grid shared once."""
    search, _browse = _pages(cli, monkeypatch)
    for part in PICK_PARTS:
        assert search.count(part) == 1, part
    side = search.split('<aside id="side">')[1].split("</aside>")[0]
    for wanted in ('id="eventChoice"', 'id="eventFolderIn"', 'id="sortNow"'):
        assert wanted in side
    keys = search.split('id="keys"')[1].split("</section>")[0]
    assert "set the picked files aside" in keys  # Delete sets aside here too
    assert "take back the choice made here" in keys  # T
    assert "/api/sort/forget" in search
    assert "deleteKeySets = false" not in search


def _review(template: str) -> str:
    """A review page, as rendered for its server."""
    place = DecisionsPlace(argument="decisions.json", host="decisions.json")
    return review_page(template, place, ("/api/decide", "/api/file")).decode()


@pytest.mark.parametrize("template", ["review.html.j2", "unwanted_review.html.j2"])
def test_the_burst_and_junk_reviews_are_built_from_the_same_parts(
    template: str,
) -> None:
    """0319, 0320: their shots are the shared grid; ←/→/Space change the group."""
    page = _review(template)
    for part in PICK_PARTS:
        assert page.count(part) == 1, part
    assert page.count('"use strict";') == 1
    assert "pickMoves = false;" in page  # the frame moves with ↑/↓ only
    keys = page.split('id="keys"')[1].split("</section>")[0]
    assert "set the picked files aside" in keys  # Delete
    assert "<kbd>↑</kbd> <kbd>↓</kbd></dt><dd>move the frame" in keys
    assert "pick or unpick the framed file" not in keys  # Space changes the series
    assert "<kbd>1</kbd>" not in keys  # 1…9 gave way to Delete
    top = page.split('<header id="bar">')[1].split("</header>")[0]
    assert 'id="invert"' in top


def test_the_burst_review_keeps_every_shot_with_a_button() -> None:
    """0319: A is the album key of the large view; *Keep every shot* is a button."""
    page = _review("review.html.j2")
    assert 'id="keepAll"' in page
    assert 'key === "a"' not in page
    assert "add it to the album named in the bar" in page
    top = page.split('<header id="bar">')[1].split("</header>")[0]
    assert 'id="albumBar"' in top


@pytest.mark.parametrize(
    "template", ["near_review.html.j2", "gone_review.html.j2", "pairs_review.html.j2"]
)
def test_the_group_reviews_share_the_large_view_without_picking(template: str) -> None:
    """0321: one large view (Enter, double click, ← →, F, Esc); nothing to pick."""
    page = _review(template)
    for part in (
        'id="viewerHelp"',
        "function wireCard(node, index)",
        "const VIEWER_KEYS = {",
    ):
        assert page.count(part) == 1, part
    assert "pickKeys = false;" in page
    assert '<span id="acting" hidden>' not in page  # no picking bar
    assert "showLarge(" in page
    keys = page.split('id="keys"')[1].split("</section>")[0]
    assert "open the photo large" in keys
    assert "set it aside, then the next one" not in page  # no Delete in the large view
