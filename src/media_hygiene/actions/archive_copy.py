"""`purge --to`: copy a run's quarantine elsewhere, then prove the copy (0306).

The copy of run `<run>` lands in `<target>/<run>/<drive>/…`, one folder per drive's
quarantine (`C` for the default one), so a copy back puts each file in its own
drive's quarantine. Nothing is erased here: `purge` erases a run only once
`archive_run` returned, that is once every file of it was read back from the target
equal to its source, and the source itself unchanged since the copy began.
"""

from __future__ import annotations

import os
import shutil
from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _

if TYPE_CHECKING:
    from collections.abc import Iterator

_CHUNK: Final = 1 << 20
_SHOWN: Final = 5  # files named in a refusal


class ArchiveError(OSError):
    """The copy failed or differs: the run must not be erased."""


@dataclass(frozen=True, slots=True)
class ArchiveJob:
    """One run to archive: its folder in each quarantine, by drive label, and where."""

    run: str
    sources: tuple[tuple[str, Path], ...]  # (`C`, `/quarantine/<run>`), …
    target: Path


@dataclass(frozen=True, slots=True)
class Archived:
    """What the target holds of a run, read back from it."""

    folder: Path
    files: int
    size: int


def run_files(job: ArchiveJob) -> Iterator[tuple[Path, Path]]:
    """Pair each file of the run with its place in the target.

    Args:
        job: The run.

    Yields:
        (source file, target file).
    """
    for label, folder in job.sources:
        base = job.target / job.run / label
        for root, _dirs, names in os.walk(folder):
            for name in names:
                source = Path(root) / name
                if source.is_file() and not source.is_symlink():
                    yield source, base / source.relative_to(folder)


def archive_run(job: ArchiveJob) -> Archived:
    """Copy the run to the target, then check every byte of it.

    Args:
        job: The run.

    Returns:
        What the target holds of it.

    Raises:
        ArchiveError: A file could not be copied, or its copy differs, or it
            changed during the copy (the run must stay).
    """
    pairs = list(run_files(job))
    before = {source: _signature(source) for source, _copy in pairs}
    try:
        for source, copy in pairs:
            copy.parent.mkdir(parents=True, exist_ok=True)
            shutil.copy2(source, copy)
    except OSError as exc:
        raise ArchiveError(
            _("The copy to {target} failed: {reason}.").format(
                target=job.target, reason=exc.strerror or exc
            )
        ) from exc
    wrong = [
        source
        for source, copy in pairs
        if _signature(source) != before[source] or not same_bytes(source, copy)
    ]
    if wrong:
        names = ", ".join(str(path) for path in wrong[:_SHOWN])
        raise ArchiveError(
            _("{count} files differ from their copy in {target}: {names}.").format(
                count=len(wrong), target=job.target, names=names
            )
        )
    size = sum(copy.stat().st_size for _source, copy in pairs)
    return Archived(job.target / job.run, len(pairs), size)


def same_bytes(source: Path, copy: Path) -> bool:
    """Compare two files byte for byte.

    Args:
        source: The original.
        copy: Its copy.

    Returns:
        True when both exist with the same content.
    """
    try:
        if source.stat().st_size != copy.stat().st_size:
            return False
        with source.open("rb") as first, copy.open("rb") as second:
            while chunk := first.read(_CHUNK):
                if chunk != second.read(len(chunk)):
                    return False
            return not second.read(1)
    except OSError:
        return False


def _signature(path: Path) -> tuple[int, int] | None:
    """The size and modification time of a file, None when it is gone.

    Args:
        path: The file.

    Returns:
        (size, mtime in ns).
    """
    try:
        stat = path.stat()
    except OSError:
        return None
    return stat.st_size, stat.st_mtime_ns


def missing_space(target: Path, needed: int) -> int:
    """Tell how many bytes the target lacks for a copy.

    Args:
        target: The folder copied to (it may not exist yet).
        needed: Bytes to copy.

    Returns:
        Bytes missing; 0 when it fits.
    """
    existing = target
    while not existing.exists() and existing != existing.parent:
        existing = existing.parent
    return max(0, needed - shutil.disk_usage(existing).free)
