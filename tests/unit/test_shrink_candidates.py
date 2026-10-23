"""`shrink`: which videos are worth lightening, the size expected, the command."""

from __future__ import annotations

import json
from pathlib import Path

from media_hygiene.config.shrink_settings import ShrinkSettings
from media_hygiene.shrink.candidates import Selection, candidates
from media_hygiene.shrink.encode import Encoding, encoding_of, ffmpeg_command
from media_hygiene.shrink.estimate import estimated_size

_ROOT = Path("/data/c/Videos")
_MJPEG = {"codec": "mjpeg", "duration": 60.0, "width": 640, "height": 480}
_PHONE = {"codec": "h264", "duration": 60.0, "width": 1920, "height": 1080}


def _row(name: str, size: int, facts: dict[str, object]) -> tuple[str, int, int, str]:
    """An index row of a video, 30 frames per second."""
    return (str(_ROOT / name), size, 1, json.dumps({"frame_rate": "30/1", **facts}))


def _names(selection: Selection, *rows: tuple[str, int, int, str]) -> list[str]:
    """The names chosen."""
    return [found.path.name for found in candidates(rows, selection)]


def test_old_codecs_and_wasteful_bit_rates_only() -> None:
    """MJPEG always; H.264 only above the bits per pixel; never a photo."""
    selection = Selection(ShrinkSettings(), (_ROOT,))
    phone = _row("phone.mp4", 100_000_000, {**_PHONE, "bit_rate": 15_000_000})
    wasteful = _row("wasteful.mp4", 999, {**_PHONE, "bit_rate": 40_000_000})
    old = _row("old.avi", 90_000_000, _MJPEG)
    photo = _row("photo.jpg", 5_000_000, _MJPEG)
    assert _names(selection, phone, wasteful, old, photo) == ["old.avi", "wasteful.mp4"]


def test_untouchable_elsewhere_short_or_tried_are_left_out() -> None:
    """Protected, outside the folders asked, under a second, or not worth it."""
    tried = _row("tried.avi", 90_000_000, _MJPEG)
    selection = Selection(
        ShrinkSettings(),
        (_ROOT,),
        (_ROOT / "Kept",),
        frozenset({(tried[0], tried[1], tried[2])}),
    )
    rows = (
        _row("Kept/kept.avi", 90_000_000, _MJPEG),
        ("/data/d/Other/far.avi", 90_000_000, 1, tried[3]),
        _row("short.avi", 90_000, {**_MJPEG, "duration": 0.5}),
        _row("unknown.avi", 90_000_000, {"codec": "mjpeg"}),
        tried,
        _row("left.avi", 90_000_000, _MJPEG),
    )
    assert _names(selection, *rows) == ["left.avi"]


def test_the_largest_gain_first() -> None:
    """The biggest file first, for the same picture."""
    selection = Selection(ShrinkSettings(), (_ROOT,))
    rows = (_row("small.avi", 50_000_000, _MJPEG), _row("big.avi", 90_000_000, _MJPEG))
    assert _names(selection, *rows) == ["big.avi", "small.avi"]


def test_estimate_smaller_when_lighter() -> None:
    """At most 720 lines: 1080p is estimated lighter; 480p, the same as by default."""
    full = estimated_size(60.0, (1920, 1080, 30.0), None)
    lighter = estimated_size(60.0, (1920, 1080, 30.0), 720)
    assert lighter < full
    small = estimated_size(60.0, (640, 480, 30.0), 720)
    assert small == estimated_size(60.0, (640, 480, 30.0), None)


def test_the_command_keeps_tags_and_fits_only_when_lighter() -> None:
    """Every sound track, the tags, MP4; the scale filter with --lighter only."""
    files = (Path("/v/a.avi"), Path("/v/a.mp4.media-hygiene.tmp"))
    same = ffmpeg_command("ffmpeg", files, Encoding(18, None, "medium", 2))
    assert "-vf" not in same
    assert same[-1] == str(files[1])
    for part in ("0:a?", "-map_metadata", "libx264", "aac", "mp4", "18", "2"):
        assert part in same
    lighter = encoding_of(ShrinkSettings(threads=3), lighter=True)
    assert (lighter.crf, lighter.lines, lighter.threads) == (23, 720, 3)
    fitted = ffmpeg_command("ffmpeg", files, lighter)
    assert "720" in fitted[fitted.index("-vf") + 1]
    assert encoding_of(ShrinkSettings(), lighter=False).threads >= 1
