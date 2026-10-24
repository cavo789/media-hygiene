"""`shrink`: which videos are worth lightening, the size expected, the command."""

from __future__ import annotations

import json
from dataclasses import replace
from pathlib import Path

import pytest

from media_hygiene.config.shrink_settings import ShrinkSettings
from media_hygiene.constants import MediaKind
from media_hygiene.index.facts import FileFacts
from media_hygiene.scan.file_check import Need, need_of
from media_hygiene.scan.metadata import IMAGE_METADATA_VERSION, METADATA_VERSION
from media_hygiene.scan.models import MediaFile
from media_hygiene.scan.video_meta import SHRUNK_TAG, video_metadata
from media_hygiene.shrink.candidates import Selection, candidates
from media_hygiene.shrink.encode import Encoding, encoding_of, ffmpeg_command, mark_of
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


def test_a_video_carrying_the_mark_is_never_a_candidate() -> None:
    """Lightened already: left out whatever its codec, rate or path (0308)."""
    selection = Selection(ShrinkSettings(bits_per_pixel=0.0001), (_ROOT,))
    marked = {**_MJPEG, "shrunk": "media-hygiene shrink crf=18"}
    rows = (_row("Moved/clip.mp4", 90_000_000, marked), _row("old.avi", 9, _MJPEG))
    assert _names(selection, *rows) == ["old.avi"]


def test_the_command_writes_the_mark_the_probe_reads() -> None:
    """Its own key, never the camera's comment; read back from the format's tags."""
    files = (Path("/v/a.avi"), Path("/v/a.mp4.media-hygiene.tmp"))
    lighter = Encoding(23, 720, "medium", 2)
    command = ffmpeg_command("ffmpeg", files, lighter)
    written = command[command.index(f"{SHRUNK_TAG}={mark_of(lighter)}") - 1]
    assert written == "-metadata"
    assert mark_of(lighter) == "media-hygiene shrink crf=23 lines=720"
    assert not any(part.startswith("comment=") for part in command)
    tags = {"comment": "Panasonic", SHRUNK_TAG: mark_of(lighter)}
    probe = {"format": {"tags": tags}, "streams": []}
    assert video_metadata(probe).shrunk == mark_of(lighter)
    assert video_metadata({"format": {"tags": {"comment": "x"}}}).shrunk is None


@pytest.mark.parametrize(
    ("kind", "need"), [(MediaKind.VIDEO, Need.CHECK), (MediaKind.IMAGE, Need.NOTHING)]
)
def test_only_videos_are_read_again_for_the_mark(kind: MediaKind, need: Need) -> None:
    """The mark is a video's: no photo header is read again for it."""
    file = MediaFile(Path("/data/c/a"), 10, 1, kind)
    known = FileFacts(visual_checked=True).with_integrity(None, "")
    older = replace(known, metadata_version=IMAGE_METADATA_VERSION)
    assert IMAGE_METADATA_VERSION < METADATA_VERSION
    assert need_of(file, older) is need
    current = replace(known, metadata_version=METADATA_VERSION)
    assert need_of(file, current) is Need.NOTHING
