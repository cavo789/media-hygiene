"""A reversible choice asks nothing (0521): the toast's Undo replaces `confirm`.

Every `window.confirm` left in the served templates is listed here with why nothing
takes its action back (or why it stays for now); a new one fails until it is named.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.page_render import render_page

_SOURCES: Final = Path(__file__).parents[2] / "src" / "media_hygiene"
_CONFIRM: Final = re.compile(r"window\.confirm\(")
# File → confirmations kept: nothing takes them back, or their Undo needs a route
# (0521 PARTIAL).
_KEPT: Final = {
    "places/templates/places.html.j2": 2,  # a place given photos / deleted
    "review/templates/phone_review.js.j2": 2,  # the phone page (phone rule)
    "search/templates/events_rule.js.j2": 1,  # rules removed from config.toml
    "search/templates/events_choice.js.j2": 1,  # leaving with unsaved choices
    "share/templates/album.js.j2": 2,  # an album deleted, a photo taken out
    "share/templates/album_edit.js.j2": 1,  # all taken out: album removed
}


def test_only_the_listed_confirmations_remain() -> None:
    """The batch choices of the reviews ask nothing any more."""
    found = {
        str(path.relative_to(_SOURCES)): len(_CONFIRM.findall(path.read_text("utf-8")))
        for path in _SOURCES.rglob("*.j2")
    }
    assert {name: n for name, n in found.items() if n} == _KEPT


@pytest.mark.parametrize("template", ["review.html.j2", "near_review.html.j2"])
def test_the_reviews_carry_the_shared_toast_once(
    template: str, monkeypatch: pytest.MonkeyPatch
) -> None:
    """One toast, its Undo button, 8 s; called once the file is read back."""
    monkeypatch.setenv(LAUNCHER_STEPS_VARIABLE, "1")
    page = render_page(template)
    assert page.count('id="mhUndoToast"') == 1
    assert "const UNDO_TOAST_MS = 8000;" in page
    assert "window.mhUndoToast(fill(" in page


def test_near_pairs_undo_clears_the_groups_it_decided() -> None:
    """G then Undo: the same groups written back undecided (`null`)."""
    page = render_page("near_review.html.j2")
    assert "() => decide(ranks, null), { keys: true }" in page


def test_validated_series_undo_through_the_pages_own_history() -> None:
    """The review's Z and the toast's Undo take back the same batch."""
    page = render_page("review.html.j2")
    assert "}), undo);" in page
    assert "window.mhUndoToast.hide();" in page
