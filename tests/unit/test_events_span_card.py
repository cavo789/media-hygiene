"""0574: the Events card of an index event: one sentence, three buttons."""

from __future__ import annotations

import re

from tests.support.page_render import render_page


def _card(page: str) -> str:
    return page.split('<div id="spanChoice" hidden>')[1].split("</div>", maxsplit=1)[0]


def test_three_buttons_in_order_and_undo_hidden() -> None:
    """Sort here now, Another folder…, Do not sort this event; Undo hidden at first."""
    card = _card(render_page("search.html.j2"))
    ids = re.findall(r'<button type="button" id="(span\w+)"', card)
    assert ids[:4] == ["spanSort", "spanOther", "spanLeave", "spanUndo"]
    assert ids[4:] == ["spanAlbum", "spanTv"]  # the shortcuts, after them (0523)
    assert 'id="spanUndo" class="plain" hidden' in card
    assert "<kbd>" not in card  # the letters are in the keys panel
    assert 'id="spanRule"' in card  # a plain link, not a sort action


def test_another_folder_is_the_bars_dialog_and_sort_goes_to_the_next() -> None:
    """No second folder form: the bar's *Move to an event…*; a move, then the next."""
    page = render_page("search.html.j2")
    assert 'byId("moveOpen").click();' in page
    sort = page.split("const spanSort = async () => {")[1].split("const spanOther")[0]
    assert sort.index("MOVE_PATHS.move") < sort.index("spanAfterMove(current, false);")
    assert "spanNext(at)" in page
    keys = page.split('id="keys"')[1].split("</section>")[0]
    assert "Sort here now" in keys
