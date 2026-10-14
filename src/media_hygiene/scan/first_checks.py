"""How long the files checked for the first time take, told once the pace is known.

The integrity pass is the long one of a first audit: every photo is decoded once. Its
first seconds are timed, then the rest is estimated from that pace, by count of files
(not bytes: a video is probed, not decoded, whatever its size). Facts only: what to say
of them is the reporter's business.
"""

from __future__ import annotations

import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Protocol

from media_hygiene.constants import MediaKind

if TYPE_CHECKING:
    from collections.abc import Callable, Sequence

    from media_hygiene.scan.models import MediaFile

# Long enough for the pool to warm up and the pace to settle, short enough to be told
# while the user still watches the screen.
SAMPLE_SECONDS: Final = 20.0


@dataclass(frozen=True, slots=True)
class FirstChecks:
    """The files a pass checks for the first time, by kind, and how long they take."""

    photos: int
    videos: int
    seconds_left: float = 0.0

    @classmethod
    def of(cls, files: Sequence[MediaFile]) -> FirstChecks:
        """Count the photos (RAW included) and the videos among the files.

        Args:
            files: The files to check.

        Returns:
            Their counts, no estimate yet.
        """
        videos = sum(file.kind is MediaKind.VIDEO for file in files)
        return cls(photos=len(files) - videos, videos=videos)

    @property
    def total(self) -> int:
        """How many files are checked.

        Returns:
            The photos and the videos.
        """
        return self.photos + self.videos


class CheckReporter(Protocol):
    """Told what the integrity pass learns about its own cost."""

    def first_checks(self, checks: FirstChecks) -> None:
        """The pace of the first checks is known: how long the rest takes.

        Args:
            checks: The files of the pass and the seconds left, estimated.
        """

    def nothing_new(self, cached: int) -> None:
        """Every file was known to the index: nothing to check.

        Args:
            cached: How many files were taken from the index.
        """


class SilentReporter:
    """A reporter that says nothing (tests, other commands)."""

    def first_checks(self, checks: FirstChecks) -> None:
        """Ignore the estimate.

        Args:
            checks: Unused.
        """

    def nothing_new(self, cached: int) -> None:
        """Ignore the warm pass.

        Args:
            cached: Unused.
        """


@dataclass(slots=True)
class Pace:
    """Times the first files of a pass, then tells the estimate once."""

    checks: FirstChecks
    tell: Callable[[FirstChecks], None]
    clock: Callable[[], float] = time.monotonic
    started: float = field(init=False)
    done: int = field(default=0, init=False)
    told: bool = field(default=False, init=False)

    def __post_init__(self) -> None:
        """Start timing now."""
        self.started = self.clock()

    def one_done(self) -> None:
        """Count one file checked; once the sample is long enough, tell the rest."""
        self.done += 1
        elapsed = self.clock() - self.started
        if self.told or elapsed < SAMPLE_SECONDS:
            return
        self.told = True
        left = elapsed / self.done * (self.checks.total - self.done)
        self.tell(FirstChecks(self.checks.photos, self.checks.videos, left))
