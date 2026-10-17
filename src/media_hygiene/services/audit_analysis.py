"""The audit's analysis of the files listed: integrity first, then exact duplicates."""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING

from media_hygiene.scan.stopwatch import Stage

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.scan.broken import BrokenFileFinder, IntegrityFindings
    from media_hygiene.scan.exact import ExactDuplicateFinder
    from media_hygiene.scan.models import DuplicateGroup, MediaFile
    from media_hygiene.scan.stopwatch import Stopwatch


@dataclass(frozen=True, slots=True)
class Finders:
    """The two passes over the files, and the stopwatch that times them."""

    broken: BrokenFileFinder
    exact: ExactDuplicateFinder
    stopwatch: Stopwatch


async def analyse(
    files: Sequence[MediaFile], finders: Finders
) -> tuple[tuple[DuplicateGroup, ...], IntegrityFindings]:
    """Find broken files first (describing images), then exact duplicates.

    Broken and empty files are kept out of duplicate groups: they are handled on their
    own (deleted when empty, quarantined when unreadable). So are the files the disk
    or the cloud could not read this time: `clean` leaves them where they are.

    Args:
        files: Every media file found.
        finders: Integrity checker, duplicate finder and stopwatch.

    Returns:
        The duplicate groups, the broken files and the visual facts of images.
    """
    with finders.stopwatch.timing(Stage.INTEGRITY):
        integrity = await finders.broken.find(files)
    broken_paths = {item.file.path for item in integrity.broken}
    broken_paths |= {item.file.path for item in integrity.unread}
    healthy = [
        file for file in files if file.size > 0 and file.path not in broken_paths
    ]
    with finders.stopwatch.timing(Stage.DIGESTS):
        groups = await finders.exact.find(healthy)
    return groups, integrity
