"""The pace of the first checks: timed on the first files, told once."""

from __future__ import annotations

from pathlib import Path

from media_hygiene.constants import MediaKind
from media_hygiene.scan.first_checks import (
    SAMPLE_SECONDS,
    FirstChecks,
    Pace,
    SilentReporter,
)
from media_hygiene.scan.models import MediaFile


def _file(name: str, kind: MediaKind) -> MediaFile:
    """A media file of the given kind."""
    return MediaFile(Path(f"/data/c/{name}"), 1, 0, kind)


class Clock:
    """A clock the test moves by hand."""

    def __init__(self) -> None:
        """Start at zero."""
        self.now = 0.0

    def __call__(self) -> float:
        """Tell the time."""
        return self.now


def test_raw_files_count_as_photos_and_videos_apart() -> None:
    """Photos and RAW files are decoded alike; videos are probed."""
    files = [
        _file("a.jpg", MediaKind.IMAGE),
        _file("b.nef", MediaKind.RAW),
        _file("c.mp4", MediaKind.VIDEO),
    ]
    checks = FirstChecks.of(files)
    assert (checks.photos, checks.videos, checks.total) == (2, 1, 3)


def test_the_rest_is_told_once_the_sample_is_long_enough() -> None:
    """Nothing before the sample; then the rest at the pace measured, once."""
    clock, told = Clock(), list[FirstChecks]()
    pace = Pace(FirstChecks(photos=90, videos=10), told.append, clock)
    clock.now = SAMPLE_SECONDS / 2
    pace.one_done()
    assert not told
    clock.now = SAMPLE_SECONDS
    pace.one_done()  # 2 files in 20 s: 98 left take 980 s
    clock.now = SAMPLE_SECONDS * 2
    pace.one_done()
    assert told == [FirstChecks(photos=90, videos=10, seconds_left=980.0)]


def test_a_pass_shorter_than_the_sample_tells_nothing() -> None:
    """A quick pass needs no estimate."""
    told = list[FirstChecks]()
    pace = Pace(FirstChecks(photos=3, videos=0), told.append, Clock())
    for _ in range(3):
        pace.one_done()
    assert not told


def test_the_silent_reporter_says_nothing() -> None:
    """Other commands and tests keep the scan quiet."""
    reporter = SilentReporter()
    reporter.first_checks(FirstChecks(photos=1, videos=0))
    reporter.nothing_new(1)
