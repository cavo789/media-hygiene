"""How sure a group of near duplicates is: moved by --tier near, or to check."""

from __future__ import annotations

from pathlib import Path
from types import MappingProxyType

import pytest

from media_hygiene.constants import MediaKind
from media_hygiene.plan.near_levels import in_messaging_folder, with_levels
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


@pytest.mark.parametrize(
    ("folder", "messaging"),
    [
        ("Android/Media/WhatsApp Images/Sent", True),
        ("Telegram Desktop", True),
        ("Email", True),
        ("Outlook Attachments", True),
        ("Pièces jointes", True),
        ("2019/Vacances", False),
        ("Signal", True),
        ("Signalisation", False),  # whole words only
    ],
)
def test_messaging_folders(folder: str, *, messaging: bool) -> None:
    """Any folder of the path counts, whole names, any case."""
    assert in_messaging_folder(DATA / folder / "a.jpg") is messaging
