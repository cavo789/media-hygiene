"""The kept version of near duplicates, and the sentence that says why."""

from __future__ import annotations

from pathlib import Path
from typing import TYPE_CHECKING

from media_hygiene.constants import KeepReason, MediaKind, NearReason
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.near_keeper import choose_keeper
from media_hygiene.plan.similar_models import NearDecision
from media_hygiene.report.near_reasons import near_why
from media_hygiene.scan.models import MediaFile

if TYPE_CHECKING:
    from collections.abc import Callable

DATA = Path("/data/c/Spectacle 2023")
FULL_HD = 1080 * 1920


def video(name: str, size: int, mtime_ns: int = 0) -> MediaFile:
    """A video of `size` bytes."""
    return MediaFile(DATA / name, size, mtime_ns, MediaKind.VIDEO)


def pixels_of(small: MediaFile | None = None) -> Callable[[MediaFile], int]:
    """Full HD for every version, except `small`."""
    return lambda file: 640 * 360 if file == small else FULL_HD


def test_the_highest_resolution_wins() -> None:
    """Even against a larger file."""
    small, big = video("small.mp4", 500), video("big.mp4", 100)
    choice = choose_keeper([small, big], pixels_of(small), KeepPolicy())
    assert (choice.keeper, choice.reason) == (big, NearReason.RESOLUTION)
    decision = NearDecision(big, (small,))
    assert near_why(decision, pixels_of(small)) == "Kept: the highest resolution."


def test_a_larger_file_by_one_percent_or_more_wins() -> None:
    """Same resolution: 2 % larger is less compressed."""
    first, second = video("IMG_1234_1.mp4", 100_000), video("IMG_1234.mp4", 102_000)
    choice = choose_keeper([first, second], pixels_of(), KeepPolicy())
    assert (choice.keeper, choice.reason) == (second, NearReason.SIZE)
    decision = NearDecision(second, (first,), reason=NearReason.SIZE)
    assert "a larger file by 2.0 KB" in near_why(decision, pixels_of())


def test_under_one_percent_the_usual_rules_choose() -> None:
    """1.7 KB of 109 MB says nothing: the oldest version wins, not the larger."""
    copy = video("IMG_1234_1_1.mp4", 114_597_601, mtime_ns=2)
    other = video("IMG_1234_1.mp4", 114_595_831, mtime_ns=1)
    choice = choose_keeper([copy, other], pixels_of(), KeepPolicy())
    assert choice.keeper == other
    assert choice.reason is NearReason.RULES
    assert choice.rule is KeepReason.OLDEST
    decision = NearDecision(other, (copy,), reason=choice.reason, rule=choice.rule)
    why = near_why(decision, pixels_of())
    assert "sizes 1.7 KB apart (under 1 %)" in why
    assert "the oldest date" in why
