"""The banner never says the place twice (0473)."""

from __future__ import annotations

import pytest

from media_hygiene.slideshow.chapters import Chapter, told_place


@pytest.mark.parametrize(
    ("name", "place", "told"),
    [
        ("Valkenburg", "Valkenburg", ""),
        ("Promenade à Valkenburg", "Valkenburg", ""),
        ("Durbuy", "Ardennes", "Ardennes"),
        ("Fête à Liège", "liege", ""),
        ("LIEGE", "Liège", ""),
        ("Saint-Jean de Luz", "Saint Jean-de-Luz", ""),
        ("Valkenburgerweg", "Valkenburg", "Valkenburg"),
        ("", "Valkenburg", "Valkenburg"),
        ("Durbuy", "", ""),
    ],
)
def test_told_place(name: str, place: str, told: str) -> None:
    """A place the name already contains is dropped; another one is kept."""
    assert told_place(name, place) == told


def test_chapter_view_drops_the_repeated_place() -> None:
    """The pages receive the place once."""
    view = Chapter(1, "Promenade à Valkenburg", "October 2026", "Valkenburg").view()
    assert view["place"] == ""
