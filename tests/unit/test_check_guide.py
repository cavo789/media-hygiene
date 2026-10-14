"""What a first audit says of its cost, and of the next audit."""

from __future__ import annotations

import io

import pytest
from rich.console import Console

from media_hygiene.console.output import Output
from media_hygiene.constants import Locale
from media_hygiene.i18n import using
from media_hygiene.scan.first_checks import FirstChecks
from media_hygiene.services.check_guide import (
    FIRST_CHECKS_TOLD,
    CheckGuide,
    rough_duration,
)

_MANY = FirstChecks(photos=2345, videos=12, seconds_left=1130.0)


def _guide(*, kept: bool) -> tuple[CheckGuide, io.StringIO]:
    """A guide printing to memory."""
    stream = io.StringIO()
    console = Console(file=stream, width=400, no_color=True)
    return CheckGuide(Output(console), kept=kept), stream


def test_many_first_checks_say_how_long_and_that_stopping_is_safe() -> None:
    """Above the threshold: the counts, the estimate, Ctrl+C, the next audit."""
    guide, stream = _guide(kept=True)
    guide.first_checks(_MANY)
    guide.close()
    shown = stream.getvalue()
    assert "2,345 photos and 12 videos to check for the first time: about 20 min." in (
        shown
    )
    assert "Ctrl+C" in shown
    assert "Next audit: a few seconds" in shown


def test_without_a_kept_cache_nothing_is_promised() -> None:
    """A cache lost with the container: no Ctrl+C promise, no fast next audit."""
    guide, stream = _guide(kept=False)
    guide.first_checks(_MANY)
    guide.close()
    shown = stream.getvalue()
    assert "The cache is not kept" in shown
    assert "Ctrl+C" not in shown
    assert "Next audit" not in shown


def test_a_few_first_checks_say_nothing() -> None:
    """Below the threshold the pass is short: no line, no closing line."""
    guide, stream = _guide(kept=True)
    guide.first_checks(FirstChecks(FIRST_CHECKS_TOLD - 1, 0, 600.0))
    guide.close()
    assert not stream.getvalue()


@pytest.mark.parametrize(
    ("checks", "named"),
    [
        (FirstChecks(600, 0), "600 photos to check"),
        (FirstChecks(0, 600), "600 videos to check"),
        (FirstChecks(1, 600), "1 photo and 600 videos to check"),
    ],
)
def test_the_files_are_named_by_kind(checks: FirstChecks, named: str) -> None:
    """A kind with no file is left out; singular and plural."""
    guide, stream = _guide(kept=True)
    guide.first_checks(checks)
    assert named in stream.getvalue()


def test_a_warm_audit_says_everything_came_from_the_cache() -> None:
    """Nothing to check: the count taken from the cache."""
    guide, stream = _guide(kept=True)
    guide.nothing_new(52056)
    assert "No new or changed file since the last audit: 52,056 files" in (
        stream.getvalue()
    )


@pytest.mark.parametrize(
    ("seconds", "said"),
    [
        (5, "less than a minute"),
        (60, "about 1 min"),
        (61, "about 2 min"),
        (600, "about 10 min"),
        (601, "about 15 min"),
        (1130, "about 20 min"),
        (3500, "about 1 h"),
        (3601, "about 1 h 15"),
        (5 * 3600, "about 5 h"),
    ],
)
def test_estimates_are_rounded_up(seconds: float, said: str) -> None:
    """To the minute, then to 5 min, then to the quarter of an hour."""
    assert rough_duration(seconds) == said


def test_the_lines_are_translated() -> None:
    """French users read French, with French separators."""
    guide, stream = _guide(kept=True)
    with using(Locale.FR):
        guide.first_checks(_MANY)
        guide.nothing_new(52056)
        guide.close()
    shown = stream.getvalue()
    assert "2.345 photos et 12 vidéos" in shown
    assert "52.056 fichiers" in shown
    assert "Prochain audit" in shown
