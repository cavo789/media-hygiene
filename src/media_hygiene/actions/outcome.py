"""Results of `clean` and `undo`: what was done, skipped or failed — and why."""

from __future__ import annotations

import errno
import os
import time
from dataclasses import dataclass, field
from typing import TYPE_CHECKING

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path


@dataclass(frozen=True, slots=True)
class Incident:
    """A file left untouched, with the translated reason."""

    path: Path
    reason: str


@dataclass(slots=True)
class Tally:
    """Mutable counters filled while acting, frozen into an outcome at the end."""

    done: int = 0
    bytes_done: int = 0
    quarantined: int = 0
    skipped: list[Incident] = field(default_factory=list[Incident])
    failed: list[Incident] = field(default_factory=list[Incident])
    started: float = field(default_factory=time.monotonic)
    folders_removed: int = 0  # left empty by a clean (0202)

    def freeze(self) -> Outcome:
        """Snapshot the counters.

        Returns:
            The immutable outcome.
        """
        return Outcome(
            done=self.done,
            bytes_done=self.bytes_done,
            quarantined=self.quarantined,
            skipped=tuple(self.skipped),
            failed=tuple(self.failed),
            seconds=time.monotonic() - self.started,
            folders_removed=self.folders_removed,
        )


@dataclass(frozen=True, slots=True)
class Outcome:
    """Final counts of a `clean` or `undo` run."""

    done: int
    bytes_done: int
    quarantined: int
    skipped: tuple[Incident, ...]
    failed: tuple[Incident, ...]
    seconds: float = 0.0
    folders_removed: int = 0  # left empty by a clean, removed (0202)


def combine(outcomes: Sequence[Outcome]) -> Outcome:
    """Sum the outcomes of several runs acted on together (a sort undone whole).

    Args:
        outcomes: The outcome of each run.

    Returns:
        One outcome: counts and durations summed, incidents of every run.
    """
    return Outcome(
        done=sum(outcome.done for outcome in outcomes),
        bytes_done=sum(outcome.bytes_done for outcome in outcomes),
        quarantined=sum(outcome.quarantined for outcome in outcomes),
        skipped=tuple(item for outcome in outcomes for item in outcome.skipped),
        failed=tuple(item for outcome in outcomes for item in outcome.failed),
        seconds=sum(outcome.seconds for outcome in outcomes),
        folders_removed=sum(outcome.folders_removed for outcome in outcomes),
    )


def why(exc: Exception) -> str:
    """Say in plain words why an action failed: never a path, never `[Errno n]`.

    The line that shows the reason already names the file (in its Windows form): the
    container path and the error number that `str(exc)` adds mean nothing to a user.
    Our own `OSError(_("..."))` messages, without an error number, pass unchanged.
    The raw error stays in the debug log.

    Args:
        exc: The error met.

    Returns:
        The translated reason.
    """
    if not isinstance(exc, OSError) or exc.errno is None:
        return str(exc)
    reasons = {
        errno.EPERM: _("not allowed (the owner or the permissions of the file)"),
        errno.EACCES: _("not allowed (the owner or the permissions of the file)"),
        errno.ENOSPC: _("the disk is full"),
        errno.EEXIST: _("something of that name is already there"),
        errno.ENOENT: _("it is no longer there"),
        errno.EROFS: _("the folder is mounted read-only (:ro)"),
        errno.ENOTEMPTY: _("the folder is not empty"),
        errno.EBUSY: _("another program is using it"),
        errno.EIO: _("the disk could not be read or written (input/output error)"),
    }
    return reasons.get(exc.errno) or exc.strerror or os.strerror(exc.errno)
