"""Burst proposals: blurrier, nearly identical, missed exposure; obvious series."""

from __future__ import annotations

from typing import Final

import pytest

from media_hygiene.config.review_settings import ReviewSettings
from media_hygiene.plan.burst_proposals import (
    AsideReason,
    Proposal,
    ProposalLimits,
    ShotLook,
    is_obvious,
    propose,
)
from media_hygiene.scan.exposure import Exposure
from media_hygiene.services.policy import proposal_limits

LIMITS: Final = proposal_limits(ReviewSettings())
SHARP: Final = 1000.0
FINE: Final = Exposure(brightness=120.0, dark_share=0.01, bright_share=0.01)
SCENE: Final = 0b1010_1100


def look(
    sharpness: float = SHARP, phash: int = SCENE, exposure: Exposure | None = FINE
) -> ShotLook:
    """A shot of the scene, sharp and well exposed unless told otherwise."""
    return ShotLook(sharpness, phash, exposure)


def best(phash: int = SCENE) -> ShotLook:
    """The sharpest shot of a series: always kept."""
    return ShotLook(SHARP * 2, phash, FINE, keep=True)


def other_scene(bits: int) -> int:
    """The scene's hash with its lowest `bits` bits flipped."""
    return SCENE ^ ((1 << bits) - 1)


def test_a_far_blurrier_shot_is_proposed() -> None:
    """Below the share of the sharpest: blurrier, whatever it looks like."""
    proposals = propose((best(), look(SHARP / 10, other_scene(30))), LIMITS)
    assert proposals == {1: Proposal(AsideReason.BLURRIER)}


def test_a_near_identical_shot_names_the_sharper_one_kept() -> None:
    """A repeat of a sharper kept shot: identical, naming it; a different one stays."""
    looks = (look(SHARP, other_scene(20)), best(), look(SHARP * 0.9, other_scene(2)))
    assert propose(looks, LIMITS) == {2: Proposal(AsideReason.IDENTICAL, 1)}


def test_a_repeat_is_compared_with_the_shots_kept_only() -> None:
    """Three repeats: the two less sharp both point to the sharpest, not a chain."""
    looks = (
        best(),
        look(SHARP * 0.9, other_scene(2)),
        look(SHARP * 0.8, other_scene(3)),
    )
    proposals = propose(looks, LIMITS)
    assert {rank: found.like for rank, found in proposals.items()} == {1: 0, 2: 0}


@pytest.mark.parametrize(
    ("exposure", "reason"),
    [
        (Exposure(220.0, 0.0, 0.05), AsideReason.OVEREXPOSED),
        (Exposure(30.0, 0.05, 0.0), AsideReason.UNDEREXPOSED),
        (Exposure(125.0, 0.0, 0.40), AsideReason.OVEREXPOSED),
        (Exposure(115.0, 0.40, 0.0), AsideReason.UNDEREXPOSED),
    ],
)
def test_a_missed_exposure_is_proposed(exposure: Exposure, reason: AsideReason) -> None:
    """Far from the others' brightness, or far more clipped: over or under."""
    looks = (
        best(),
        look(phash=other_scene(30)),
        look(phash=other_scene(40), exposure=exposure),
    )
    assert propose(looks, LIMITS) == {2: Proposal(reason)}


def test_of_two_shots_only_the_one_farther_from_mid_gray_is_missed() -> None:
    """Two shots far apart in brightness: the well exposed one stays."""
    dark = Exposure(20.0, 0.0, 0.0)
    looks = (best(), look(phash=other_scene(30), exposure=dark))
    assert propose(looks, LIMITS) == {1: Proposal(AsideReason.UNDEREXPOSED)}
    bright_best = ShotLook(SHARP * 2, SCENE, dark, keep=True)
    assert not propose((bright_best, look(phash=other_scene(30))), LIMITS)


def test_zero_disables_each_reason() -> None:
    """Every threshold at 0: nothing is ever proposed."""
    looks = (
        best(),
        look(SHARP / 10, other_scene(30)),
        look(phash=other_scene(1)),
        look(phash=other_scene(40), exposure=Exposure(250.0, 0.0, 0.9)),
    )
    assert not propose(looks, ProposalLimits())


def test_kept_shots_are_never_proposed() -> None:
    """The sharpest and protected shots stay, however alike or blurry."""
    protected = ShotLook(SHARP / 10, SCENE, FINE, keep=True)
    assert not propose((best(), protected), LIMITS)


def test_obvious_only_when_nothing_is_left_to_judge() -> None:
    """Obvious: something proposed, and only kept shots left; else to look at."""
    repeat = look(SHARP * 0.9, other_scene(1))
    different = look(SHARP * 0.9, other_scene(30))
    for looks, obvious in (
        ((best(), repeat), True),
        ((best(), repeat, different), False),
        ((best(), different), False),
    ):
        assert is_obvious(looks, propose(looks, LIMITS)) is obvious
