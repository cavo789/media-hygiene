"""The search page's fixed layout (0463): nothing appears or disappears with a pick."""

from __future__ import annotations

import re

from tests.support.page_render import render_page


def _bar(page: str) -> str:
    return page.split('<header id="bar">')[1].split("</header>", maxsplit=1)[0]


def test_the_actions_stay_in_the_bar_greyed_while_nothing_is_picked() -> None:
    """The lead and the actions both shown; the script greys them instead of hiding."""
    page = render_page("search.html.j2")
    assert "#bar > #lead[hidden], #bar > #acting[hidden] { display: flex; }" in page
    assert (
        'for (const id of ["unpick", "setAside", "invert"]) $(id).disabled = !some;'
        in page
    )
    assert "#bar::before" in page  # the break between the two lines


def test_show_and_sorted_are_segmented_in_the_left_column() -> None:
    """No select for Show, Sorted or Words of: buttons; sources in the syntax."""
    page = render_page("search.html.j2")
    side = page.split('id="toc"')[1].split("</section>")[0]
    for field in ("kind", "sorting"):
        assert f'<input type="hidden" id="{field}"' in side
        assert f'<select id="{field}"' not in page
    assert 'id="source"' not in page
    assert "folder:durbuy" in page.split('id="syntax"')[1]


def test_the_thumbnail_sizes_are_in_the_bar() -> None:
    """S, M, L: kept per viewer, the photo only at S."""
    page = render_page("search.html.j2")
    sizes = re.findall(r'data-for="size" data-value="(\w)"', _bar(page))
    assert sizes == ["s", "m", "l"]
    assert 'main[data-size="s"] .meta { display: none; }' in page


def test_the_panel_lists_invert_under_more_keys_and_floats_it() -> None:
    """I in *More keys*; opened, it floats over the page and Esc closes it."""
    page = render_page("search.html.j2")
    panel = page.split('id="keys"')[1].split("</section>")[0]
    shown, more = panel.split('id="moreKeys"')
    assert "<kbd>I</kbd>" not in shown
    assert "<kbd>I</kbd>" in more
    assert "#moreKeys[open] > dl { position: fixed;" in page
    assert 'event.key === "Escape" && more.open' in page


def test_more_files_load_on_scroll_and_search_stays_in_sight() -> None:
    """An observer on the end of the grid; 🔍 sticky at the bottom of the form."""
    page = render_page("search.html.j2")
    assert '.observe($("moreLine"))' in page
    assert "#go { position: sticky; bottom: 0;" in page
