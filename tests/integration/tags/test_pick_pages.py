"""`library`, `browse`, the reviews: one page of photos to pick, same keys and bar."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

import pytest

from media_hygiene import review as templates
from media_hygiene.review.place import DecisionsPlace
from media_hygiene.services.review_file import review_page
from tests.support.pick_pages import PICK_PARTS
from tests.support.search_page import serve_search
from tests.support.visible_controls import visible_controls

if TYPE_CHECKING:
    from typer.testing import CliRunner


# The shared parts, as each one shows in the page served (review/templates/pick_*).
_SHARED = (
    *PICK_PARTS,
    '#bar::before { content: ""; order: 2',  # pick_bar.css.j2: the same two lines
    '<select id="order">',  # pick_order.html.j2: Sort by (0347)
    '<dialog id="mhAsk"',  # ask_dialog.html.j2: the one question (0663)
    '<div id="mhSay"',  # busy_say.html.j2: working, done, failed (0664)
    "window.mhView = Object.freeze(",  # view_state.html.j2: the view in the URL (0666)
    '<button type="button" id="mhStepChip"',  # step_chip.html.j2: a step running (0661)
)


def _pages(cli: CliRunner, monkeypatch: pytest.MonkeyPatch) -> tuple[str, str]:
    """The search page and the folder view, as served."""
    answers = serve_search(
        cli, monkeypatch, [("GET /library", None), ("GET /browse", None)]
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
        # Show: a select on the folder view, buttons in the search's left column (0463).
        assert (
            page.count('<select id="kind">') + page.count('id="kind" value="all"') == 1
        )


def test_set_aside_and_apply_end_the_second_line_of_every_page(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """The shared rules fix their place; the album and the rest are panels."""
    page = _pages(cli, monkeypatch)[0]
    assert "#acting > #setAside { order: 9; margin-left: auto; }" in page
    assert "#bar > #applyBar { order: 10;" in page
    assert '<details id="albumBar" class="barPanel">' in page
    assert "reference-albums/" in page.split('id="albumBar"')[1].split("albumName")[1]
    assert '<details id="moveBar" class="barPanel closesOnChoice">' in page


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
    assert "next event to decide" in keys  # U (0574 dropped T)
    assert "/api/sort/forget" in search
    for wanted in ('id="trialTry"', 'id="trialUndo"', 'id="trialRest"'):  # 0640
        assert wanted in side
    # Declared before the page's first search reads it.
    assert search.index("let trialAgain") < search.index("function reopen(")
    assert "deleteKeySets = false" not in search
    # 0457: two tabs on top of the left column, the events' one hidden at first.
    assert (
        side.index('id="tabPhotos"')
        < side.index('id="tabEvents"')
        < side.index('id="toc"')
    )
    assert 'role="tabpanel" aria-labelledby="tabEvents" hidden' in side
    assert 'localStorage.setItem("mh-search-tab"' in search
    # 0558: the late photos of an event, in the Events view, added or refused.
    for wanted in ('id="lateList"', 'id="lateAdd"', 'id="lateRefuse"'):
        assert wanted in side
    assert "/api/late-events/refuse" in search


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
    assert (
        "set it aside, then the previous one" not in page
    )  # no Delete in the large view


def test_the_large_view_preloads_its_neighbours_once_and_gently(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0675: one preload at a time, none for a video or save-data, dropped on a jump."""
    search, _browse = _pages(cli, monkeypatch)
    preload = search.split("function preloadAround() {")[1].split("\n}\n")[0]
    assert "navigator.connection.saveData" in preload
    assert "!file.video" in preload
    assert "preloadStop();" in preload  # a jump drops what waits
    assert search.count("new Image()") >= 1
    shown = search.split("function open() {\n  const file = files[current];")[1]
    assert "preloadAround();" in shown.split("\n}\n")[0]


def test_the_large_view_arrows_step_over_the_files_set_aside() -> None:
    """0517: ← → Home End: the nearest file not set aside; Delete: the previous."""
    page = _review("near_review.html.j2")
    assert "if (!files[index].chosen) return index;" in page
    for key in (
        "ArrowRight: () => largeAt(notAside(current, 1)),",
        "ArrowLeft: () => largeAt(notAside(current, -1)),",
        "Home: () => largeAt(notAside(-1, 1)),",
        "End: () => largeAt(notAside(files.length, -1)),",
    ):
        assert key in page, key
    assert "const before = notAside(index, -1);" in page
    assert "before >= 0 ? before : notAside(index, 1)" in page


def _bar_tag(page: str, ident: str) -> str:
    """The opening tag of the bar's button `ident`."""
    return (
        page.split(f'id="{ident}"', maxsplit=1)[0].rsplit("<button", 1)[1]
        + page.split(f'id="{ident}"')[1].split(">", maxsplit=1)[0]
    )


def test_the_bar_buttons_wear_their_role(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """0542: Set aside red and last, the move first and filled, Apply now filled."""
    search, _browse = _pages(cli, monkeypatch)
    pages = [search] + [
        _review(name) for name in ("review.html.j2", "unwanted_review.html.j2")
    ]
    for page in pages:
        assert 'class="danger"' in _bar_tag(page, "setAside")
        acting = page.split('<span id="acting" hidden>')[1].split("</span>")[0]
        assert acting.rstrip().endswith("</button>")
        assert acting.rindex("<button") == acting.index('id="setAside"') - len(
            "<button "
        )
    assert (
        "button.danger { color: var(--mk-on-danger); background: var(--bad)" in search
    )
    move = search.split('<details id="moveMenu"')[1].split("</summary>")[0]
    assert '<summary class="primary"' in move
    assert "Move to an event…" in search
    acting = search.split('<span id="acting" hidden>')[1].split("</span>")[0]
    assert acting.index('id="moveMenu"') < acting.index('id="invert"')
    apply_now = Path(templates.__file__).with_name("templates") / "apply_now.html.j2"
    assert "plain" not in _bar_tag(apply_now.read_text(encoding="utf-8"), "applyNow")


# The menus of line 2 (0665), in this order on every page of tiles (one list, CSS).
_MENU_ORDER = (
    "#acting > #moveMenu { order: 4; }",
    "#bar > #albumBar, #bar > #albumQuick { order: 5; }",
    "#bar > #showBar { order: 6; }",
    "#bar > #moveBar { order: 7; }",
    "#acting > #invert { order: 8; }",
)
# Controls visible at load on /library, counted from the HTML (visible_controls):
# 46 before 0665 (2026-11-11), 33 after; a new one must find its place in a menu.
_MOST_VISIBLE = 33


def test_the_bar_menus_come_in_one_order_and_open_by_the_keyboard(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Move, Album, Slideshow, Describe, Invert; entries carry their letter (0665)."""
    search = _pages(cli, monkeypatch)[0]
    places = [search.index(rule) for rule in _MENU_ORDER]
    assert places == sorted(places)
    for ident, letters in (("moveMenu", "EM"), ("moveBar", "TDP")):
        menu = search.split(f'<details id="{ident}"')[1].split("</details>")[0]
        assert [f'data-key="{letter}"' in menu for letter in letters] == [True] * len(
            letters
        )
    assert 'event.key === "ArrowDown"' in search
    assert "[data-key]::after { content: attr(data-key);" in search


def test_the_less_used_filters_fold_and_an_active_one_stays_a_chip(
    cli: CliRunner, monkeypatch: pytest.MonkeyPatch
) -> None:
    """Words, dates, path shown; the rest under More filters; their chips (0565)."""
    search = _pages(cli, monkeypatch)[0]
    side = search.split('<aside id="side">')[1].split("</aside>")[0]
    folded = side.split('<details id="moreFilters">')[1].split("</details>\n")[0]
    for ident in (
        'id="albumIn"',
        'id="kind"',
        'id="sorting"',
        'id="missing"',
        'id="placeIn"',
    ):
        assert ident in folded
    for ident in ('id="text"', 'id="from"', 'id="folder"'):
        assert ident not in folded
    for chip in ("body.album.inside !== null", 'body.sorting !== "all"', "body.place"):
        assert chip in search
    assert visible_controls(search) <= _MOST_VISIBLE
