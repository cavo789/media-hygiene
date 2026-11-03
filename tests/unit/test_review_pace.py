"""Review bars: time left at the user's pace, share of the gain seen (0527, 0530)."""

from __future__ import annotations

from pathlib import Path
from types import SimpleNamespace
from typing import TYPE_CHECKING, Final

import pytest

from media_hygiene.services.review_file import review_page

if TYPE_CHECKING:
    from media_hygiene.review.place import DecisionsPlace

_TEMPLATES: Final = Path(__file__).parents[2] / "src/media_hygiene/review/templates"
_PAGES: Final = ("review.html.j2", "near_review.html.j2", "pairs_review.html.j2")


def _page(template: str) -> str:
    place: DecisionsPlace = SimpleNamespace(  # type: ignore[assignment]
        argument="decisions.json", host="C:\\decisions.json"
    )
    return review_page(template, place, ("/api/decide", "/api/file")).decode()


def test_the_pace_leaves_idle_gaps_out_and_waits_ten_cases() -> None:
    """A gap over a minute adds nothing; before ten cases, the count only."""
    script = (_TEMPLATES / "review_pace.js.j2").read_text(encoding="utf-8")
    assert "const paceIdle = 60000;" in script
    assert "const paceFloor = 10;" in script
    assert "now - state.at <= paceIdle ? now - state.at : 0" in script
    assert "state.decided < paceFloor" in script


@pytest.mark.parametrize("template", _PAGES)
def test_each_review_page_shows_the_pace_and_the_share_seen(template: str) -> None:
    """Bursts, near duplicates and folder pairs share the one bar line."""
    page = _page(template)
    assert page.count("const pacedFrom = ") == 1
    assert 'id="eta"' in page
    assert "paceLine(" in page
    assert "seenShare(" in page
    assert "% of the {total} seen" in page


def test_pairs_offer_the_biggest_gain_first_ties_by_name() -> None:
    """The pairs page orders by bytes freed, or by folder pair; ties by rank."""
    page = _page("pairs_review.html.j2")
    assert '<option value="gain">' in page
    assert '<option value="name">' in page
    assert "(pairs[b].size - pairs[a].size) || a - b" in page
    assert 'localStorage.setItem("pairs-order", kind)' in page


def test_the_burst_page_opens_on_the_sheet_sized_to_the_window() -> None:
    """Obvious series left: the contact sheet first, rows from the window's height."""
    page = _page("review.html.j2")
    assert "if (obviousTodo().length > 0) openSheet();" in page
    assert "Math.floor((height - top) / each)" in page
    assert "const sheetFewest = 3;" in page
