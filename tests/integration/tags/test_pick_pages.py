"""`search` and `browse`: one page of photos to pick, same gestures, keys and bar."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.services.sort_reviewing import open_sort_review, sort_page
from tests.integration.tags.test_search_albums import _serve
from tests.support.pick_pages import PICK_PARTS
from tests.support.sort_review import classified

if TYPE_CHECKING:
    import pytest
    from typer.testing import CliRunner

    from media_hygiene.paths.locations import Locations

# The shared parts, as each one shows in the page served (review/templates/pick_*).
_SHARED = (
    'id="views"',  # pick_views.html.j2
    *PICK_PARTS,
    "#bar #albumBar { flex-basis: 100%",  # pick_grid.css.j2: the bar keeps its height
)


def _pages(cli: CliRunner, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    """The search page and the folder view, as served."""
    answers = _serve(cli, monkeypatch, [("GET /search", None), ("GET /browse", None)])
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
    """The form under the views, the keys below it; the bar holds the picking."""
    search, _ = _pages(cli, monkeypatch)
    side = search.split('<aside id="side">')[1].split("</aside>")[0]
    assert side.index('id="views"') < side.index('id="form"') < side.index('id="keys"')
    assert 'href="/browse"' in side.split('id="views"')[1].split("</div>")[0]
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
    search, browse = _pages(cli, monkeypatch)
    sent = search.split("async function search(event, again) {")[1].split("\n}\n")[0]
    assert "document.activeElement.blur()" in sent
    assert "showFiles(found.hits, again)" in sent  # a save keeps the cards
    assert "function scope() {\n  return asked;" in search
    assert "function scope() {\n  return { folder: folder };" in browse


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
