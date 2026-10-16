"""Before a clean: files copied from another drive into the quarantine, and the room.

Two `-v` mounts are two filesystems in the container, so every file set aside is
copied, then removed (`actions/no_overwrite.py`). From the same drive the space comes
back at once; from another drive, the whole size lands on the quarantine's drive (with
the launcher, `C:`, often the smallest).
"""

from __future__ import annotations

import shutil
from collections import defaultdict
from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import BrokenReason
from media_hygiene.paths.drives import Drives, QuarantineRoute

if TYPE_CHECKING:
    from collections.abc import Iterator
    from pathlib import Path

    from media_hygiene.plan.models import CleanPlan
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.services.runtime import Runtime

# Left free on the quarantine's drive: a full system drive breaks Windows itself.
QUARANTINE_HEADROOM: Final = 1024**3


@dataclass(frozen=True, slots=True)
class CrossDrive:
    """The files one quarantine receives from other drives than its own."""

    quarantine: Path
    drive: str  # the quarantine's, e.g. `C:`
    sources: tuple[str, ...]  # the drives the files come from, e.g. (`E:`,)
    count: int
    size: int


@dataclass(frozen=True, slots=True)
class Room:
    """What a quarantine receives from other drives, and the free space there."""

    cross: CrossDrive
    free: int

    @property
    def missing(self) -> int:
        """Bytes to free before the copies fit, the headroom kept.

        Returns:
            Zero when they fit.
        """
        return max(0, self.cross.size + QUARANTINE_HEADROOM - self.free)


def quarantine_route(runtime: Runtime) -> QuarantineRoute:
    """The quarantine each file goes to, and the drives of the mounts.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        The route of this run.
    """
    drives = Drives(runtime.mounts.host_sources)
    return QuarantineRoute(drives, runtime.locations.quarantine_dir)


def set_aside(plan: CleanPlan) -> Iterator[MediaFile]:
    """List the files `clean` moves to the quarantine (not those it deletes).

    Args:
        plan: What would be cleaned.

    Yields:
        Each file moved: copies (unless `--delete` deletes them), near duplicates,
        burst shots set aside, unreadable files and orphan sidecars.
    """
    for decision in plan.decisions:
        yield from (file for file in decision.removable if plan.to_quarantine(file))
    for near in plan.near:
        yield from near.removable
    for choice in plan.bursts:
        yield from choice.discarded
    yield from (
        item.file for item in plan.broken if item.reason is not BrokenReason.EMPTY
    )
    yield from plan.orphans


def cross_drive(route: QuarantineRoute, files: Iterator[MediaFile]) -> list[Room]:
    """Group the files copied to another drive by the quarantine receiving them.

    Args:
        route: Which quarantine receives each file, and the drives.
        files: The files set aside.

    Returns:
        One room per quarantine receiving files from another drive; none when no
        drive is known (Linux, named volumes), every file stays on its drive, or the
        free space cannot be read.
    """
    counts: defaultdict[Path, list[int]] = defaultdict(lambda: [0, 0])
    sources: defaultdict[Path, set[str]] = defaultdict(set)
    drives: dict[Path, str] = {}
    for file in files:
        crossing = route.crosses_drive(file.path)
        if crossing is None:
            continue
        quarantine = route.receiving(file.path)
        drives[quarantine] = crossing[1]
        sources[quarantine].add(crossing[0])
        counts[quarantine][0] += 1
        counts[quarantine][1] += file.size
    rooms = (
        (
            CrossDrive(folder, drive, tuple(sorted(sources[folder])), *counts[folder]),
            free_space(folder),
        )
        for folder, drive in sorted(drives.items())
    )
    return [Room(cross, free) for cross, free in rooms if free is not None]


def free_space(folder: Path) -> int | None:
    """Free bytes on the filesystem of a folder (on Docker Desktop: the host drive).

    Args:
        folder: The quarantine.

    Returns:
        The free bytes; None when they cannot be read.
    """
    try:
        return shutil.disk_usage(folder).free
    except OSError:
        return None
