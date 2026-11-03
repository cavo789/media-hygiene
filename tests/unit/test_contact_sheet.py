"""The contact sheet (0520, 0529): the same keys and script on every page with one."""

from __future__ import annotations

import re

import pytest

from tests.support.page_render import render_page

SHEET_PAGES = ("review.html.j2", "near_review.html.j2")


def _sheet_keys(page: str) -> list[str]:
    """The rows of the keys panel shown only while the contact sheet is open."""
    return re.findall(
        r'<dt class="sheet-only">(.*?)</dt><dd class="sheet-only">(.*?)</dd>', page
    )


def test_every_contact_sheet_lists_the_same_keys() -> None:
    """Enter, click, double click and Z mean the same for bursts and near duplicates."""
    keys = [_sheet_keys(render_page(template)) for template in SHEET_PAGES]
    assert len(keys[0]) == 4
    assert keys[0] == keys[1]


@pytest.mark.parametrize("template", SHEET_PAGES)
def test_each_contact_sheet_measures_its_rows_with_the_shared_script(
    template: str,
) -> None:
    """The rows a screen holds come from the one shared script, included once."""
    page = render_page(template)
    assert page.count("const sheetFit = ") == 1
    assert 'id="sheetOpen"' in page


def test_the_near_sheet_saves_a_screen_in_one_write() -> None:
    """Enter posts the rows shown, each with its own action, in one request."""
    page = render_page("near_review.html.j2")
    assert "decideEach(choices, nextScreen)" in page
    assert 'action: flips.has(rank) ? "swap" : "planned"' in page
