"""The "10 minutes of tidying" session (0528): chained pages, tile, empty page."""

from __future__ import annotations

from pathlib import Path
from typing import Final

from media_hygiene.review.step_watch import BURSTS_PAGE, NEAR_REVIEW_PAGE

_TEMPLATES: Final = (
    Path(__file__).resolve().parents[2] / "src/media_hygiene/review/templates"
)


def test_bursts_lead_to_near_and_near_ends_the_chain() -> None:
    """The order the session walks, in the templates."""
    bursts = (_TEMPLATES / "review.html.j2").read_text("utf-8")
    near = (_TEMPLATES / "near_review.html.j2").read_text("utf-8")
    assert f'tidy_next = "{NEAR_REVIEW_PAGE}"' in bursts
    assert 'tidy_next = ""' in near
    assert BURSTS_PAGE == "/review/bursts/"


def test_the_bar_offers_going_on_stopping_and_says_what_next() -> None:
    """At the limit: the question; stopped: one What next, Apply now named."""
    text = (_TEMPLATES / "tidy_bar.html.j2").read_text("utf-8")
    assert "const MINUTES = 10" in text
    assert "showModal" in text
    assert "What next: Apply now" in text
