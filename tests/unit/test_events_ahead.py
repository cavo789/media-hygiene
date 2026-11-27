"""0652: Events tab: the next event prefetched, the last one resumed."""

from __future__ import annotations

from tests.support.page_render import render_page


def test_next_event_prefetched_after_each_grid() -> None:
    """The grid of an event made from the index asks for the next one once shown."""
    page = render_page("search.html.j2")
    span = page.split("const loadSpan = async (index) => {")[1]
    assert span.index("showFiles(view.hits, false);") < span.index("ahead(index);")
    assert "image.src = hit.preview;" in page


def test_last_event_kept_per_browser_tab_and_resumed() -> None:
    """The event shown is kept in sessionStorage; the list resumes on it."""
    page = render_page("search.html.j2")
    assert "sessionStorage.setItem(LAST_EVENT, card.id)" in page
    assert page.count("remember(") >= 2
    assert page.count("resume();") == 1
    assert "localStorage.setItem(LAST_EVENT" not in page
