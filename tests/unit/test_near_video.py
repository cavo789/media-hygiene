"""Re-encoded videos, from their fingerprints alone."""

from __future__ import annotations

from dataclasses import replace
from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.plan.keeper import KeepPolicy
from media_hygiene.plan.near_video import is_near_video, video_near_decisions
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.video_models import FrameHash, VideoLook, VideoPrint

DATA = Path("/data/c")
SCENES = (
    0x0F0F_3C3C_5A5A_6969,
    0x3C3C_0F0F_6969_5A5A,
    0x5A5A_6969_0F0F_3C3C,
    0x6969_5A5A_3C3C_0F0F,
    0x0FF0_3CC3_5AA5_6996,
)
OTHER = tuple(scene ^ 0xFFFF_FFFF_0000_0000 for scene in SCENES)
DATE = "2024-05-01T10:00:00.000000Z"


def video(name: str, size: int = 100) -> MediaFile:
    """A video below /data/c."""
    return MediaFile(DATA / name, size, 0, MediaKind.VIDEO)


def look(width: int = 1920, scenes: tuple[int, ...] = SCENES) -> VideoLook:
    """A 30-second 16:9 video showing these scenes, with the reference date."""
    frames = tuple(FrameHash(scene, scene) for scene in scenes)
    return VideoLook(
        VideoPrint(frames), 30.0, width, width * 9 // 16, DATE, codec="h264"
    )


def names(files: tuple[MediaFile, ...]) -> list[str]:
    """File names, for readable assertions."""
    return [file.path.name for file in files]


def test_the_highest_resolution_is_kept_and_unrelated_videos_stay() -> None:
    """A smaller re-encoded copy goes; another video of the same length is no copy."""
    files = [video("small.mp4"), video("big.mov"), video("other.mp4")]
    looks = {
        DATA / "small.mp4": replace(look(640), duration=30.3, codec="hevc"),
        DATA / "big.mov": look(1920),
        DATA / "other.mp4": look(1920, OTHER),
    }
    (decision,) = video_near_decisions(files, looks, KeepPolicy())
    assert decision.keeper.path.name == "big.mov"
    assert names(decision.removable) == ["small.mp4"]


def test_length_and_proportions_must_agree() -> None:
    """Two seconds longer, or square instead of 16:9: not the same video."""
    files = [video("big.mp4"), video("longer.mp4"), video("square.mp4")]
    looks = {
        DATA / "big.mp4": look(),
        DATA / "longer.mp4": replace(look(640), duration=32.0),
        DATA / "square.mp4": replace(look(640), height=640),
    }
    assert not video_near_decisions(files, looks, KeepPolicy())


def test_one_frame_may_differ_not_two() -> None:
    """A cut between two frame timings is tolerated once."""
    one_off = (*SCENES[:4], OTHER[4])
    two_off = (*SCENES[:3], *OTHER[3:])
    assert is_near_video(look(), look(640, one_off))
    assert not is_near_video(look(), look(640, two_off))


def test_blank_frames_tell_nothing() -> None:
    """Frames black in both are left out; black in one only, they differ."""
    blank_end = (*SCENES[:3], 0, 0)
    blank_start = (0, 0, 0, 0, SCENES[4])
    assert is_near_video(look(1920, blank_end), look(640, blank_end))
    assert not is_near_video(look(), look(640, blank_end))
    assert not is_near_video(look(1920, blank_start), look(640, blank_start))


def test_dates_must_match_or_be_lost() -> None:
    """Another take of a still scene keeps its own date; a copy may lose it."""
    later = replace(look(640), recorded_at="2024-05-01T10:05:00Z")
    undated = replace(look(640), recorded_at=None)
    truncated = replace(look(640), recorded_at="2024-05-01T10:00:00Z")
    assert not is_near_video(look(), later)
    assert is_near_video(look(), undated)
    assert is_near_video(look(), truncated)
    assert not is_near_video(undated, look(640))


def test_protected_copies_are_listed_but_kept() -> None:
    """A copy in a protected folder is never removable; alone, it makes no decision."""
    files = [video("big.mp4"), video("master/small.mp4")]
    looks = {DATA / "big.mp4": look(), DATA / "master/small.mp4": look(640)}
    policy = KeepPolicy(protected=(DATA / "master",))
    assert not video_near_decisions(files, looks, policy)
    files.append(video("copy.mp4"))
    looks[DATA / "copy.mp4"] = look(320)
    (decision,) = video_near_decisions(files, looks, policy)
    assert names(decision.removable) == ["copy.mp4"]
    assert names(decision.protected) == ["small.mp4"]


def test_videos_without_a_fingerprint_are_ignored() -> None:
    """Only fingerprinted videos are compared."""
    files = [video("big.mp4"), video("unknown.mp4")]
    assert not video_near_decisions(files, {DATA / "big.mp4": look()}, KeepPolicy())
