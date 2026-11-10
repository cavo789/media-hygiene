"""A reversible choice asks nothing (0521): the toast's Undo replaces `confirm`.

What nothing takes back asks through the one in-page dialog (0663): no native box is
left, and each question is listed here with why it is not a toast.
"""

from __future__ import annotations

import re
from pathlib import Path
from typing import Final

import pytest

from media_hygiene.services.next_command import LAUNCHER_STEPS_VARIABLE
from tests.support.page_render import render_page

_SOURCES: Final = Path(__file__).parents[2] / "src" / "media_hygiene"
_NATIVE: Final = re.compile(r"\b(?:window\.)?(?:confirm|alert|prompt)\(")
# Every former native box (0663): the shared ask dialog, and why nothing takes it back.
_ASKED: Final = {
    "places/templates/places.html.j2": 2,  # photos given to a place; a place deleted
    "review/templates/phone_review.js.j2": 2,  # phone files deleted; one not kept
    "search/templates/events_rule.js.j2": 1,  # rules removed from config.toml
    "search/templates/events_choice.js.j2": 1,  # leaving with an unsaved folder: save?
    "review/templates/quarantine_purge.js.j2": 1,  # a purge: nothing brings it back
    "review/templates/shrink.js.j2": 1,  # hours of encoding start (0586's one question)
    "share/templates/album.js.j2": 2,  # albums deleted; a photo out (no Undo route)
    "share/templates/album_edit.js.j2": 1,  # all taken out: the album removed
    "review/templates/home.js.j2": 1,  # every paired device forgotten (0683)
}


def _templates() -> dict[str, str]:
    return {
        str(path.relative_to(_SOURCES)): path.read_text("utf-8")
        for path in _SOURCES.rglob("*.j2")
    }


def test_no_native_box_is_left() -> None:
    """No `window.confirm`, `alert` nor `prompt` in any template (0663)."""
    found = {name: _NATIVE.findall(text) for name, text in _templates().items()}
    assert {name: hits for name, hits in found.items() if hits} == {}


def test_every_question_is_the_shared_dialog() -> None:
    """Each former confirmation asks through `window.mhAsk`, listed with its reason."""
    found = {
        name: text.count("window.mhAsk(")
        for name, text in _templates().items()
        if "ask_dialog" not in name
    }
    assert {name: n for name, n in found.items() if n} == _ASKED


@pytest.mark.parametrize(
    "template",
    ["quarantine.html.j2", "phone_review.html.j2", "album.html.j2",
     "places.html.j2", "search.html.j2", "shrink.html.j2", "album_edit.html.j2"],
)  # fmt: skip
def test_the_pages_that_ask_carry_the_dialog_once(template: str) -> None:
    """One dialog, the safe button first and focused, every line set as text."""
    page = render_page(template)
    assert page.count('<dialog id="mhAsk"') == 1
    assert "noButton.focus();" in page
    assert "paragraph.textContent = line;" in page


def test_the_home_page_carries_the_dialog_once() -> None:
    """The home page is not on the frame: it includes the dialog itself."""
    home = (_SOURCES / "review" / "templates" / "home.html.j2").read_text("utf-8")
    assert home.count('{% include "ask_dialog.html.j2" %}') == 1


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
