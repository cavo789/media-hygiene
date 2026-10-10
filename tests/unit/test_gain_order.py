"""The largest space first, with a running total: these groups = 90 % of the space."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.plan.similar_models import NearDecision, SureReason
from media_hygiene.report.gain_order import gain_order, running_shares
from media_hygiene.scan.models import MediaFile


def group(name: str, freed: int, *, sure: bool = False) -> NearDecision:
    """A group whose single copy frees `freed` bytes."""
    keeper = MediaFile(Path("/data/c") / name, freed * 2, 0, MediaKind.IMAGE)
    copy = MediaFile(Path("/data/c/copies") / name, freed, 0, MediaKind.IMAGE)
    reason = SureReason.SAME_LOOK if sure else None
    return NearDecision(keeper, (copy,), sure=reason)


def test_running_shares_add_up_to_the_whole() -> None:
    """Rounded percentages of the running total; nothing freed counts as all."""
    assert running_shares([900, 50, 50]) == (90, 95, 100)
    assert running_shares([0, 0]) == (100, 100)
    assert not running_shares([])


def test_to_check_first_then_sure_each_by_space() -> None:
    """A heavy sure group still comes after the groups to check."""
    groups = [
        group("small.jpg", 10),
        group("video.mp4", 900, sure=True),
        group("large.jpg", 90),
        group("tie.jpg", 10),
    ]
    ordered = gain_order(groups)
    assert [(g.keeper.path.name, share) for g, share in ordered] == [
        ("large.jpg", 9),
        ("small.jpg", 10),
        ("tie.jpg", 11),
        ("video.mp4", 100),
    ]
