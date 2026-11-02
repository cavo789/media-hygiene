"""The search period (0453): To follows From; one click for today, month, year."""

from __future__ import annotations

import re

import pytest

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


def test_path_contains_lists_the_folders_without_moving_the_grid() -> None:
    """0471: a floating list under *Path contains*; *My folders* folded to one line."""
    page = render_page("search.html.j2")
    assert 'aria-controls="folderList"' in page
    assert 'id="folderList" class="comboList"' in page
    assert re.search(r"\.comboList \{[^}]*position: absolute", page)
    assert re.search(r"#folders\[open\] > #tree \{[^}]*position: fixed", page)
    assert "📁 My folders ▸" in page
    assert "In a folder" not in page
    for key in ('"ArrowDown"', '"ArrowUp"', '"Enter"', '"Escape"'):
        assert key in page
    assert "b.when.localeCompare(a.when)" in page  # latest first


def test_move_dialog_lists_the_event_folders_like_path_contains() -> None:
    """0487: the move dialog's names are the *Path contains* list, no datalist."""
    page = render_page("search.html.j2")
    assert "<datalist" not in page.split('id="moveDlg"')[1].split("</dialog>")[0]
    assert 'id="moveNames" class="comboList"' in page
    assert 'aria-controls="moveNames"' in page
    assert 'id="moveClear" class="plain comboClear"' in page
    assert page.count("function comboList(") == 2  # one helper (+ the album bar's copy)
    assert "count: folder.files" in page


def test_move_dialog_sources_keep_box_and_folder_on_one_line() -> None:
    """0562: the shared field width never stretches the boxes; no sideways scroll."""
    page = render_page("search.html.j2")
    assert (
        ".sources input[type=checkbox] { width: auto; flex: none; margin: 0; }" in page
    )
    assert re.search(r"\.sources label \{ display: flex !important;", page)
    assert re.search(r"#moveDlg \.moveBody \{[^}]*overflow: hidden auto", page)
    assert 'element("b", "count"' in page


@pytest.mark.parametrize(
    "template", ["search.html.j2", "people.html.j2", "review.html.j2"]
)
def test_no_native_datalist_is_left(template: str) -> None:
    """0490: every field lists through the shared combo list, its CSS not copied."""
    page = render_page(template)
    assert "<datalist" not in page
    assert ' list="' not in page
    assert "function comboAttach(" in page
    assert ".comboList { position: absolute" in page


def test_the_other_fields_get_the_combo_list() -> None:
    """0490: album, event folders (three fields), people (go to, name a group)."""
    search = render_page("search.html.j2")
    assert 'comboAttach($("albumName")' in search
    assert '["eventFolderIn", "send-category", "ruleCategory"]' in search
    people = render_page("people.html.j2")
    assert 'comboAttach($("who")' in people
    assert "comboAttach(input, () => state.people" in people


def test_period_from_two_days_and_steps() -> None:
    """0488: Shift+click on a second day sets To; ◀ ▶ move the period by its length."""
    page = render_page("search.html.j2")
    assert 'id="dayBefore"' in page
    assert 'id="dayAfter"' in page
    assert "event && event.shiftKey && dayClicked" in page
    assert "(event) => searchDay(text, event)" in page  # the large view too
    assert "act(event)" in page
    assert "steppable();" in page  # greyed while both dates are empty
