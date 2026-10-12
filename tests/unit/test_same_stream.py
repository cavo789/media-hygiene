"""Copies of the same picture and sound: chosen again by the usual keep rules."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.same_stream import with_same_streams
from media_hygiene.plan.similar_models import NearDecision
from media_hygiene.scan.models import MediaFile

DATA = Path("/data/c")
RATED = MediaFile(DATA / "Novembre 2015/162.mp4", 1_132, 0, MediaKind.VIDEO)
ORIGINAL = MediaFile(DATA / "Noël/20150704_101010.mp4", 1_000, 0, MediaKind.VIDEO)
SMALL = MediaFile(DATA / "WhatsApp/VID-20150704-WA0001.mp4", 300, 0, MediaKind.VIDEO)


def test_the_usual_rules_choose_between_same_streams() -> None:
    """The named folder wins over the larger file; the re-encoded copy still goes."""
    decision = NearDecision(RATED, (ORIGINAL, SMALL))
    streams = {RATED.path: "same", ORIGINAL.path: "same", SMALL.path: "other"}
    (chosen,) = with_same_streams((decision,), streams, KeepPolicy())
    assert chosen.keeper == ORIGINAL
    assert set(chosen.removable) == {RATED, SMALL}
    assert chosen.same_stream == {RATED.path}


def test_a_protected_copy_is_kept_and_nothing_is_left() -> None:
    """The protected copy becomes the keeper: with nothing to move, the group goes."""
    decision = NearDecision(RATED, (), (ORIGINAL,))
    streams = {RATED.path: "same", ORIGINAL.path: "same"}
    policy = KeepPolicy(protected=(DATA / "Noël",))
    (chosen,) = with_same_streams((decision,), streams, policy)
    assert chosen.keeper == ORIGINAL
    assert chosen.removable == (RATED,)
    no_copy = NearDecision(ORIGINAL, (), (RATED,))
    both = KeepPolicy(protected=(DATA / "Noël", DATA / "Novembre 2015"))
    assert not with_same_streams((no_copy,), streams, both)


def test_other_streams_leave_the_group_alone() -> None:
    """A copy re-encoded for real: resolution and size still decide."""
    decision = NearDecision(RATED, (SMALL,))
    streams = {RATED.path: "one", SMALL.path: "other"}
    assert with_same_streams((decision,), streams, KeepPolicy()) == (decision,)
