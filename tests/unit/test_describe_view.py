"""What a describing run says: photos alone, or photos and videos counted apart."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.classify.ai.describe import DescribeOutcome
from media_hygiene.console.describe_view import show_describe_counts
from media_hygiene.constants import Locale
from media_hygiene.i18n import install
from tests.support.runtime import make_runtime, output_of

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations


def said(locations: Locations, outcome: DescribeOutcome) -> str:
    """The console output of one outcome, on one line."""
    runtime = make_runtime(locations)
    show_describe_counts(runtime.output, outcome)
    return " ".join(output_of(runtime).split())


def test_photos_alone_are_called_photos(locations: Locations) -> None:
    """No video described: the sentence names photos only."""
    assert "3 photos described; kept in the cache." in said(
        locations, DescribeOutcome(described=3)
    )


def test_videos_are_named_apart(locations: Locations) -> None:
    """Videos among the described: both counts, each in its own plural."""
    printed = said(locations, DescribeOutcome(described=3, videos=1))
    assert "2 photos and 1 video described; kept in the cache." in printed


def test_french_counts_photos_and_videos(locations: Locations) -> None:
    """In French, each fragment takes its own plural."""
    install(Locale.FR)
    try:
        printed = said(locations, DescribeOutcome(described=3, videos=2))
    finally:
        install(Locale.EN)
    assert "1 photo et 2 vidéos décrites ; gardées dans le cache." in printed
