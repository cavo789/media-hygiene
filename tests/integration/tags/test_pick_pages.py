"""`search` and `browse`: one page of photos to pick, same gestures, keys and bar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services.sort_reviewing import open_sort_review, sort_page
from tests.support.pick_pages import PICK_PARTS
from tests.support.search_page import serve_search
from tests.support.sort_review import classified

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

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


def test_the_sort_review_is_built_from_the_same_parts(locations: Locations) -> None:
    """0389: review-sort's photos are the shared grid; no Delete to set aside there."""
    runtime, _workbook = classified(locations)
    page = sort_page(open_sort_review(runtime, None))
    for part in PICK_PARTS:
        assert page.count(part) == 1, part
    assert page.count('"use strict";') == 1
    top = page.split('<header id="bar">')[1].split("</header>")[0]
    assert (
        top.index('id="prevEvent"')
        < top.index('id="position"')
        < top.index('id="nextEvent"')
    )
    assert 'id="invert"' in top
    keys = page.split('id="keys"')[1].split("</section>")[0]
    assert "every photo of the event" in keys  # Ctrl+A
    assert "set the picked files aside" not in keys  # Delete takes back a choice here
    assert 'id="zoom"' not in page  # the large view replaced Z
