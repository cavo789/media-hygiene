"""What a first audit costs, said while it runs, and why the next one is fast.

Users do not read the documentation: a first audit of a large collection runs for tens
of minutes, so the tool says how long, that stopping is safe, and that the work is kept
— only when it is (a persistent `/cache`); otherwise the setup tip says how to keep it.
"""

from __future__ import annotations

import math
from typing import TYPE_CHECKING, Final, Self

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext
from media_hygiene.paths.mount_kind import MountKind

if TYPE_CHECKING:
    from media_hygiene.console.output import Output
    from media_hygiene.scan.first_checks import FirstChecks
    from media_hygiene.services.runtime import Runtime

# Below this, a first pass is short enough to need no explanation.
FIRST_CHECKS_TOLD: Final = 500
_MINUTE: Final = 60
_HOUR: Final = 3600
# Estimates are rounded up, generously: to the minute up to 10 min, then to 5 min,
# then to the quarter of an hour.
_FINE_MINUTES: Final = 10
_COARSE_MINUTES: Final = 5
_HOUR_MINUTES: Final = 15


class CheckGuide:
    """Says what the integrity pass of an audit costs, and what the next one will."""

    def __init__(self, output: Output, *, kept: bool) -> None:
        """Bind the guide to the console.

        Args:
            output: Where to print.
            kept: Whether the index survives the container (a persistent `/cache`).
        """
        self._output = output
        self._kept = kept
        self._long = False

    @classmethod
    def of(cls, runtime: Runtime) -> Self:
        """Guide the audit of this run, on its console.

        Args:
            runtime: Settings, mount points and output.

        Returns:
            A guide that knows whether the cache is kept.
        """
        return cls(runtime.output, kept=runtime.persistent(MountKind.CACHE))

    def first_checks(self, checks: FirstChecks) -> None:
        """Say how long the first checks take, when there are many of them.

        Args:
            checks: The files of the pass and the seconds left, estimated.
        """
        if checks.total < FIRST_CHECKS_TOLD:
            return
        self._long = True
        files = _files_to_check(checks)
        about = rough_duration(checks.seconds_left)
        if self._kept:
            text = _(
                "{files} to check for the first time: {about}. You can stop at any "
                "time (Ctrl+C): what is checked is kept, and the next audit takes "
                "seconds."
            )
        else:
            text = _(
                "{files} to check for the first time: {about}. The cache is not "
                "kept: the next audit checks them all again (see the tip at the end)."
            )
        self._output.info(f"⏳ {text.format(files=files, about=about)}")

    def nothing_new(self, cached: int) -> None:
        """Say that every file came from the cache.

        Args:
            cached: How many files were taken from the index.
        """
        text = ngettext(
            "No new or changed file since the last audit: {count} file taken from "
            "the cache.",
            "No new or changed file since the last audit: {count} files taken from "
            "the cache.",
            cached,
        )
        self._output.info(f"♻️  {text.format(count=human_number(cached))}")

    def close(self) -> None:
        """After a long first pass, say what the next audit will cost."""
        if self._long and self._kept:
            self._output.info(
                "⚡ "
                + _(
                    "Next audit: a few seconds, the files checked are taken from "
                    "the cache."
                )
            )


def rough_duration(seconds: float) -> str:
    """Say a duration still to come, rounded up: `about 7 min`, `about 1 h 15`.

    Args:
        seconds: The estimate.

    Returns:
        The translated, generously rounded duration.
    """
    if seconds < _MINUTE:
        return _("less than a minute")
    minutes = math.ceil(seconds / _MINUTE)
    if minutes <= _FINE_MINUTES:
        return _("about {minutes} min").format(minutes=minutes)
    if seconds < _HOUR:
        minutes = _rounded_up(minutes, _COARSE_MINUTES)
        if minutes < _MINUTE:
            return _("about {minutes} min").format(minutes=minutes)
    hours, rest = divmod(_rounded_up(minutes, _HOUR_MINUTES), _MINUTE)
    if not rest:
        return _("about {hours} h").format(hours=hours)
    return _("about {hours} h {minutes:02d}").format(hours=hours, minutes=rest)


def _rounded_up(minutes: int, step: int) -> int:
    """Round minutes up to a multiple of a step.

    Args:
        minutes: The minutes.
        step: The multiple.

    Returns:
        The smallest multiple of `step` not below `minutes`.
    """
    return math.ceil(minutes / step) * step


def _files_to_check(checks: FirstChecks) -> str:
    """Name the files of the pass: `2,345 photos and 12 videos`.

    Args:
        checks: Their counts.

    Returns:
        The translated counts, videos left out when there are none.
    """
    photos = ngettext("{count} photo", "{count} photos", checks.photos).format(
        count=human_number(checks.photos)
    )
    if not checks.videos:
        return photos
    videos = ngettext("{count} video", "{count} videos", checks.videos).format(
        count=human_number(checks.videos)
    )
    if not checks.photos:
        return videos
    return _("{photos} and {videos}").format(photos=photos, videos=videos)
