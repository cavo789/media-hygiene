"""The frame a vision model sees of a video: where it is taken, which side is shrunk."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.classify.models import MediaInput
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.scan.video_still import VideoStill, shown_size, still_of
from media_hygiene.services.tag_work import stills_of

VIDEO = Path("/data/c/Videos/clip.mp4")


def test_the_middle_of_a_landscape_video() -> None:
    """10 s, 1920x1080: the frame at 5 s, its width shrunk."""
    meta = MediaMetadata(duration=10.0, width=1920, height=1080)
    assert still_of(VIDEO, meta, "ffmpeg") == VideoStill(
        VIDEO, 5.0, landscape=True, ffmpeg="ffmpeg"
    )


def test_a_quarter_turn_makes_a_portrait() -> None:
    """A phone's portrait video is stored wide and turned on display (90 or -90)."""
    for rotation in (90, -90, 270):
        meta = MediaMetadata(duration=4.0, width=1920, height=1080, rotation=rotation)
        still = still_of(VIDEO, meta, "ffmpeg")
        assert still is not None
        assert not still.landscape
    upside_down = MediaMetadata(duration=4.0, width=1920, height=1080, rotation=180)
    assert still_of(VIDEO, upside_down, "ffmpeg") == VideoStill(
        VIDEO, 2.0, landscape=True, ffmpeg="ffmpeg"
    )


def test_no_frame_without_a_length_or_a_size() -> None:
    """The probe read nothing: not seen; its shorter side is 0."""
    assert still_of(VIDEO, MediaMetadata(width=640, height=480), "ffmpeg") is None
    assert still_of(VIDEO, MediaMetadata(duration=3.0), "ffmpeg") is None
    assert shown_size(MediaMetadata(duration=3.0)) == 0
    assert shown_size(MediaMetadata(width=640, height=480)) == 480


def test_the_stills_of_a_run_are_those_of_its_videos() -> None:
    """Photos and unprobed videos have none; without `ffmpeg`, no video has one."""
    meta = MediaMetadata(duration=2.0, width=640, height=480)
    root = VIDEO.parent
    files = (
        MediaInput(VIDEO, root, 10, 1, None, meta),
        MediaInput(root / "other.mp4", root, 10, 1),
        MediaInput(root / "photo.jpg", root, 10, 1, None, meta),
        MediaInput(root / "unknown.mp4", root, 10, 1, None, MediaMetadata()),
    )
    expected = VideoStill(VIDEO, 1.0, landscape=True, ffmpeg="ffmpeg")
    assert stills_of(files, "ffmpeg") == {VIDEO: expected}
    assert not stills_of(files, None)
