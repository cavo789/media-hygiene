"""How sure a group of near duplicates is: moved by --tier near, or to check."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.plan.near_levels import with_levels
from media_hygiene.plan.similar_models import (
    NearDecision,
    SimilarFindings,
    SureReason,
)
from media_hygiene.report.near_reasons import level_text
from media_hygiene.scan.models import MediaFile, VisualFacts
from media_hygiene.scan.video_models import FrameHash, VideoLook, VideoPrint

DATA = Path("/data/c")
HASH = 0x0F0F_3C3C_5A5A_6969
DATE = "2021:07:05 10:00:00"


def media(name: str, size: int = 100) -> MediaFile:
    """A file below /data/c."""
    return MediaFile(DATA / name, size, 0, MediaKind.IMAGE)


def look(dhash: int = HASH, taken_at: str | None = DATE) -> VisualFacts:
    """An image of the reference scene, from the reference camera."""
    return VisualFacts(dhash, HASH, 400, 300, 100.0, taken_at, "Pixel 6")


def levelled(copies: dict[str, VisualFacts]) -> NearDecision:
    """The group of `kept.jpg` (10 KB) and these copies (1 KB each), levelled."""
    keeper = media("kept.jpg", 10_000)
    removable = tuple(media(name, 1_000) for name in copies)
    visuals = {DATA / name: facts for name, facts in copies.items()}
    visuals[keeper.path] = look()
    similar = SimilarFindings(
        near=(NearDecision(keeper, removable),), visuals=MappingProxyType(visuals)
    )
    (decision,) = with_levels(similar).near
    return decision


def test_identical_fingerprints_from_the_same_camera_are_sure() -> None:
    """Perceptual distance 0, same camera: nothing to look at."""
    decision = levelled({"Export/kept small.jpg": look()})
    assert decision.sure is SureReason.SAME_LOOK
    assert level_text(decision).startswith("Sure: identical fingerprints")


def test_a_smaller_messaging_copy_of_the_same_moment_is_sure() -> None:
    """A WhatsApp copy, one bit apart, shot at the same moment."""
    decision = levelled({"WhatsApp Images/IMG-WA0001.jpg": look(HASH ^ 1)})
    assert decision.sure is SureReason.MESSAGING_COPY
    assert "messaging or e-mail folder" in level_text(decision)


@pytest.mark.parametrize(
    "copy",
    [
        pytest.param({"WhatsApp/IMG-WA0001.jpg": look(HASH ^ 1, None)}, id="no-date"),
        pytest.param({"Holidays/small.jpg": look(HASH ^ 1)}, id="no-messaging"),
        pytest.param(
            {"WhatsApp/a.jpg": look(HASH ^ 1), "Holidays/b.jpg": look(HASH ^ 1)},
            id="one-copy-unsure",
        ),
    ],
)
def test_every_other_group_is_to_check(copy: dict[str, VisualFacts]) -> None:
    """A copy without the date, outside a messaging folder, or one unsure copy."""
    decision = levelled(copy)
    assert decision.sure is None
    assert level_text(decision).startswith("To check:")


def test_a_group_is_as_sure_as_its_least_sure_copy() -> None:
    """Identical and messaging copies: the messaging reason is told."""
    decision = levelled(
        {"Export/same.jpg": look(), "Telegram/IMG-1.jpg": look(HASH ^ 1)}
    )
    assert decision.sure is SureReason.MESSAGING_COPY


def test_a_group_without_copy_to_move_is_to_check() -> None:
    """Only protected copies: nothing moves, nothing is sure."""
    keeper = media("kept.jpg")
    decision = NearDecision(keeper, (), (media("master/kept.jpg"),))
    similar = SimilarFindings(
        near=(decision,), visuals=MappingProxyType({keeper.path: look()})
    )
    assert with_levels(similar).near[0].sure is None


def _video_look(recorded_at: str | None) -> VideoLook:
    """A video recorded at `recorded_at`."""
    return VideoLook(VideoPrint((FrameHash(HASH, HASH),)), 10.0, 640, 360, recorded_at)


def test_videos_of_the_same_stream_or_sent_by_messaging_are_sure() -> None:
    """The very picture and sound, or a smaller messaging copy of the same date."""
    keeper, stream = media("v/kept.mp4", 9_000), media("v/rated.mp4", 9_001)
    sent = media("WhatsApp Video/VID-WA0003.mp4", 2_000)
    looks = {file.path: _video_look(DATE) for file in (keeper, stream, sent)}
    similar = SimilarFindings(
        videos=(
            NearDecision(keeper, (stream,), same_stream=frozenset({stream.path})),
            NearDecision(keeper, (sent,)),
        ),
        video_looks=MappingProxyType(looks),
    )
    levels = with_levels(similar)
    assert [d.sure for d in levels.videos] == [
        SureReason.SAME_STREAM,
        SureReason.MESSAGING_COPY,
    ]
    assert levels.sure_groups == len(levels.groups)
    assert level_text(levels.videos[0]).startswith("Sure: the very picture and sound")


def test_a_whatsapp_copy_without_exif_named_the_same_day_is_sure() -> None:
    """WhatsApp stripped the EXIF: the day in its name is the proof (no time)."""
    decision = levelled(
        {"WhatsApp Images/IMG-20210705-WA0003.jpg": look(HASH ^ 1, None)}
    )
    assert decision.sure is SureReason.MESSAGING_NAME
    assert "its name dated the same day" in level_text(decision)


@pytest.mark.parametrize(
    "copy",
    [
        pytest.param(
            {"WhatsApp/IMG-20210706-WA0003.jpg": look(HASH ^ 1, None)}, id="other-day"
        ),
        pytest.param(
            {"WhatsApp/IMG-WA0003.jpg": look(HASH ^ 1, None)}, id="no-name-date"
        ),
        pytest.param(
            {"WhatsApp/IMG-20210705-WA0003.jpg": look(HASH ^ 1, "2020:01:01 10:00:00")},
            id="other-exif-date",
        ),
        pytest.param(
            {"Holidays/IMG-20210705-WA0003.jpg": look(HASH ^ 1, None)},
            id="no-messaging",
        ),
    ],
)
def test_a_name_date_alone_is_not_enough(copy: dict[str, VisualFacts]) -> None:
    """Another day, no date in the name, an EXIF date of its own, not messaging."""
    assert levelled(copy).sure is None


def test_a_kept_version_without_a_readable_date_leaves_the_copy_to_check() -> None:
    """No day on the kept side: the name has nothing to agree with."""
    keeper = media("kept.jpg", 10_000)
    sent = media("WhatsApp/IMG-20210705-WA0003.jpg", 1_000)
    visuals = {
        keeper.path: look(taken_at="not a date"),
        sent.path: look(HASH ^ 1, None),
    }
    similar = SimilarFindings(
        near=(NearDecision(keeper, (sent,)),), visuals=MappingProxyType(visuals)
    )
    assert with_levels(similar).near[0].sure is None


def test_a_whatsapp_video_named_the_day_it_was_recorded_is_sure() -> None:
    """A video's ISO time, read as a local day, agrees with `VID-…-WA0001`."""
    keeper = media("v/kept.mp4", 9_000)
    sent = media("WhatsApp Video/VID-20210705-WA0001.mp4", 2_000)
    looks = {
        keeper.path: _video_look("2021-07-05T10:00:00+0200"),
        sent.path: _video_look(None),
    }
    similar = SimilarFindings(
        videos=(NearDecision(keeper, (sent,)),), video_looks=MappingProxyType(looks)
    )
    assert with_levels(similar).videos[0].sure is SureReason.MESSAGING_NAME
