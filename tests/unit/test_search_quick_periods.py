"""The search period (0453): To follows From; one click for today, month, year."""

from __future__ import annotations

import re

from tests.support.page_render import render_page


def test_the_quick_periods_are_buttons_under_the_dates() -> None:
    """Today, this month, this year, none: each a button with its words for a reader."""
    page = render_page("search.html.j2")
    spans = re.findall(r'<button type="button" class="plain" data-span="(\w*)"', page)
    assert spans == ["day", "month", "year", ""]
    assert (
        page.index('id="to"') < page.index('class="spans"') < page.index('id="folder"')
    )
    for title in ("Today", "This month", "This year", "Any date"):
        assert f'aria-label="{title}"' in page


def test_to_follows_from_when_empty_or_earlier() -> None:
    """Never a period that ends before it starts; a later To is kept."""
    page = render_page("search.html.j2")
    assert '$("from").addEventListener("change"' in page
    assert (
        'if (from && (!$("to").value || $("to").value < from)) $("to").value = from;'
        in page
    )
