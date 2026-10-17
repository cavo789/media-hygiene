"""Town names compared without case, accents nor separators (0229)."""

from __future__ import annotations

from typing import TYPE_CHECKING

import pytest

from media_hygiene.geo.folding import fold, town_key
from media_hygiene.geo.gazetteer import Gazetteer
from tests.support.towns import write_towns

if TYPE_CHECKING:
    from pathlib import Path


@pytest.mark.parametrize(
    ("typed", "key"),
    [
        ("Saint-Jean de Luz", "saint jean de luz"),
        ("  saint_jean__de.luz ", "saint jean de luz"),
        ("L\u2019Isle-Adam", "l isle adam"),
        ("L'Isle Adam", "l isle adam"),
        ("Liège", "liege"),
    ],
)
def test_a_town_key_reads_separators_as_one_space(typed: str, key: str) -> None:
    """Hyphens, apostrophes, underscores, dots and runs of spaces: one space."""
    assert town_key(typed) == key


def test_fold_itself_keeps_the_separators() -> None:
    """`fold` is unchanged: its other callers compare more than town names."""
    assert fold("Saint-Jean de Luz") == "saint-jean de luz"


def test_the_town_search_finds_a_hyphenated_town_typed_with_spaces(
    tmp_path: Path,
) -> None:
    """The search of `places`: `saint jean de` finds Saint-Jean-de-Luz."""
    towns = Gazetteer.load(write_towns(tmp_path))
    assert [town.name for town in towns.search("saint jean de", 3)] == [
        "Saint-Jean-de-Luz"
    ]
