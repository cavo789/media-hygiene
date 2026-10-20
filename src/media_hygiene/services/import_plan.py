"""What `import` copies: the files only a backup holds, minus near copies and twins.

The audit compares the backup folders with the library (0204) and leaves out what the
user already dealt with (`backup_dealt`). Of the rest, an image whose near copy is in
the library (a HEIC on the NAS, its JPG in the photos) is listed apart, not proposed;
identical files of a backup are copied once (the first by path). Each copy goes to
`<first photo folder>/From NAS/<its folders in the backup>` (0245).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.actions.copy_in import CopyJob
from media_hygiene.constants import MediaKind
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.index.repository import FactsRepository
from media_hygiene.index.visual_listing import library_visuals
from media_hygiene.plan.backup_import import near_present
from media_hygiene.scan.image_check import inspect_image

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from media_hygiene.plan.backups import BackupCoverage
    from media_hygiene.scan.models import MediaFile, VisualFacts
    from media_hygiene.services.runtime import Runtime

# The folder of the copies, below the first photo folder (maintainer, 2026-10-20).
FROM_BACKUP: Final = "From NAS"

type Candidate = tuple[BackupCoverage, MediaFile]


@dataclass(frozen=True, slots=True)
class ImportPlan:
    """What `import` copies, and what it leaves apart (each one counted)."""

    jobs: tuple[CopyJob, ...]
    backups: tuple[BackupCoverage, ...]
    near: tuple[MediaFile, ...] = ()  # a near copy is in the library: not proposed
    twins: int = 0  # identical files of a backup: copied once

    @property
    def size(self) -> int:
        """Bytes to copy.

        Returns:
            The sum of the sources' sizes.
        """
        return sum(job.source.stat().st_size for job in self.jobs)


def plan_copies(
    runtime: Runtime, backups: tuple[BackupCoverage, ...], to: Path | None
) -> ImportPlan:
    """Decide every copy from the audit's comparison.

    Args:
        runtime: Settings, mount points and output (the index).
        backups: Each backup folder compared with the library.
        to: The folder receiving the copies (container path); None: `From NAS` in
            the first photo folder.

    Returns:
        The plan.
    """
    candidates, twins = _unique(
        [(backup, file) for backup in backups for file in backup.to_import], runtime
    )
    near = near_paths(runtime, [file for _backup, file in candidates])
    base = to or first_library_folder(runtime, backups) / FROM_BACKUP
    several = len(backups) > 1
    jobs = tuple(
        CopyJob(
            file.path,
            (base / backup.folder.name if several else base)
            / file.path.relative_to(backup.folder),
        )
        for backup, file in candidates
        if file.path not in near
    )
    apart = tuple(file for _backup, file in candidates if file.path in near)
    return ImportPlan(jobs, backups, apart, twins)


def near_paths(runtime: Runtime, files: Iterable[MediaFile]) -> frozenset[Path]:
    """The images whose near copy is in the library.

    Args:
        runtime: Settings, mount points and output (the index).
        files: The candidates.

    Returns:
        Their paths.
    """
    visuals: dict[Path, VisualFacts] = {}
    for file in files:
        if file.kind is MediaKind.IMAGE:
            visual = inspect_image(file.path).visual
            if visual is not None:
                visuals[file.path] = visual
    if not visuals:
        return frozenset()
    folders = tuple(
        runtime.mapper.to_container(f) for f in runtime.settings.folders.backups
    )
    with FactsRepository.open(runtime.index_file) as repository:
        library = library_visuals(repository.connection, folders)
    return near_present(visuals, library)


def first_library_folder(runtime: Runtime, backups: Sequence[BackupCoverage]) -> Path:
    """The first photo folder that is not a backup.

    Args:
        runtime: Settings, mount points and output.
        backups: The backup folders.

    Returns:
        Its container path.

    Raises:
        MountError: Only backup folders are mounted.
    """
    taken = {backup.folder for backup in backups}
    for root in runtime.mounts.data_roots(runtime.locations.data_dir):
        if root not in taken:
            return root
    raise MountError(
        _("No photo folder to copy into: only backup folders are mounted."),
        _("Add your photo folder: mh folders add <folder>."),
    )


def _unique(
    candidates: list[Candidate], runtime: Runtime
) -> tuple[list[Candidate], int]:
    """Keep one of identical files of the backups (the first by path).

    The audit hashed the files sharing a size; their digests are read from the index.

    Args:
        candidates: Each backup and its file to import.
        runtime: Settings, mount points and output (the index).

    Returns:
        The candidates, each content once, and how many twins were left out.
    """
    sizes: dict[int, int] = {}
    for _backup, file in candidates:
        sizes[file.size] = sizes.get(file.size, 0) + 1
    if all(count == 1 for count in sizes.values()):
        return candidates, 0
    kept: list[Candidate] = []
    seen: set[tuple[int, str]] = set()
    with FactsRepository.open(runtime.index_file) as repository:
        for backup, file in sorted(candidates, key=lambda pair: str(pair[1].path)):
            digest = repository.get(file).full_digest if sizes[file.size] > 1 else None
            key = (file.size, digest or str(file.path))
            if key not in seen:
                seen.add(key)
                kept.append((backup, file))
    return kept, len(candidates) - len(kept)
