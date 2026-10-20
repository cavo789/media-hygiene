"""The audit's analysis of the files listed: integrity first, then exact duplicates."""

from __future__ import annotations

from collections import Counter
from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.plan.backups import BackupFolders, ComparedFiles
from media_hygiene.scan.exact import partial_pass
from media_hygiene.scan.progress import Step
from media_hygiene.scan.stopwatch import Stage
from media_hygiene.services.backup_dealt import dealt_with

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.plan.backups import BackupComparison
    from media_hygiene.plan.returned import ReturnedFile
    from media_hygiene.scan.broken import BrokenFileFinder, IntegrityFindings
    from media_hygiene.scan.exact import ExactDuplicateFinder
    from media_hygiene.scan.models import MediaFile
    from media_hygiene.scan.stopwatch import Stopwatch
    from media_hygiene.services.returned import ReturnedFinder


@dataclass(frozen=True, slots=True)
class Finders:
    """The passes over the files, and the stopwatch that times them.

    `returned` recognises the files set aside by a choice that came back (0216);
    `backups` are the folders only compared with the library (0204).
    """

    broken: BrokenFileFinder
    exact: ExactDuplicateFinder
    stopwatch: Stopwatch
    returned: ReturnedFinder | None = None
    backups: BackupFolders = field(default_factory=BackupFolders)
    # The deletions waiting for `review --gone`: not proposed back from a backup (0245).
    gone: ReturnedFinder | None = None


def healthy_files(
    files: Sequence[MediaFile], integrity: IntegrityFindings
) -> list[MediaFile]:
    """Keep the files worth comparing: not empty, not broken, read this time.

    Args:
        files: Media files checked.
        integrity: What the check found.

    Returns:
        The healthy files, in their order.
    """
    broken_paths = {item.file.path for item in integrity.broken}
    broken_paths |= {item.file.path for item in integrity.unread}
    return [file for file in files if file.size > 0 and file.path not in broken_paths]


async def analyse(
    files: Sequence[MediaFile],
    finders: Finders,
    listed: Sequence[MediaFile] = (),
) -> tuple[BackupComparison, IntegrityFindings, tuple[ReturnedFile, ...]]:
    """Find broken files first (describing images), then exact duplicates.

    Broken and empty files are kept out of duplicate groups: they are handled on their
    own (deleted when empty, quarantined when unreadable). So are the files the disk
    or the cloud could not read this time: `clean` leaves them where they are. The
    files of the backup folders are only compared by content: never checked, never
    in a group, never proposed back (0204), never read whole (0274).

    Args:
        files: Every media file of the library.
        finders: Integrity checker, duplicate finder, stopwatch, backup folders.
        listed: Every media file listed, the backups' included.

    Returns:
        The library's duplicate groups and what each backup lacks or holds alone,
        the broken files and the visual facts of images, and the files set aside
        before that came back.
    """
    with finders.stopwatch.timing(Stage.INTEGRITY):
        integrity = await finders.broken.find(files)
    healthy = healthy_files(files, integrity)
    backup = [file for file in finders.backups.files_in(listed) if file.size > 0]
    with finders.stopwatch.timing(Stage.DIGESTS):
        groups = await finders.exact.find(healthy)
        returned = await finders.returned.find(healthy) if finders.returned else ()
        both = await with_partials(finders.exact, ComparedFiles(healthy, backup))
        compared = finders.backups.compare(groups, both)
        compared = await dealt_with(compared, finders)
    return compared, integrity, returned


async def with_partials(
    exact: ExactDuplicateFinder, files: ComparedFiles
) -> ComparedFiles:
    """Give the partial digest of the files a backup may share with another file.

    A backup file whose size no library file has has no copy there, and is not read
    (unless another backup file has its size: `import` copies such twins once). The
    library files of a size a backup file has are read too (the index keeps most).
    No file is read whole (0274): 128 KiB each at most.

    Args:
        exact: The exact pipeline, whose index keeps the digests.
        files: The library's healthy files and the backups' non-empty ones.

    Returns:
        The same files, with the partial digests of those candidates.
    """
    if not files.backup:
        return files
    mine = {file.size for file in files.library}
    theirs = Counter(file.size for file in files.backup)
    candidates = [
        *(f for f in files.backup if f.size in mine or theirs[f.size] > 1),
        *(f for f in files.library if f.size in theirs),
    ]
    step = Step(
        _("Comparing the backup with your photos"),
        _(
            "Reads the first and last 64 KB of the files of the same size on both "
            "sides: a backup is never read whole."
        ),
    )
    partials = await exact.digests(candidates, partial_pass(step))
    return replace(files, partials=partials)
