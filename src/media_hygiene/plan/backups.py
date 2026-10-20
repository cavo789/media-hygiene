"""Backup folders: compared by content with the library, never changed (TODO 0204).

A backup folder (`--backup`, `[folders] backups`) is listed and its files go through
the exact pipeline with the library's (size, then SHA-256): a file whose size no other
file has has no copy. Its files are then taken out of the duplicate groups, so a copy
in a backup is never the reason a library file goes, and never goes itself; the near
duplicates and the burst series never see them. Two answers per backup folder: the
library's files without an identical copy in it (`missing`), and its files without an
identical copy in the library (`only`: to copy before wiping an old disk).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import is_within
from media_hygiene.plan.backup_import import DealtWith, proposed

if TYPE_CHECKING:
    from collections.abc import Iterable, Sequence
    from pathlib import Path

    from media_hygiene.scan.models import DuplicateGroup, MediaFile
    from media_hygiene.scan.walker import Walk


@dataclass(frozen=True, slots=True)
class BackupCoverage:
    """One backup folder compared with the library, in container paths.

    `missing`: the library's files without an identical copy in this folder;
    `only`: this folder's files without an identical copy in the library.
    """

    folder: Path
    files: int = 0
    missing: tuple[MediaFile, ...] = ()
    only: tuple[MediaFile, ...] = ()
    # Of `only`, the contents the user already dealt with (0245, `backup_import`).
    dealt: DealtWith = field(default_factory=DealtWith)

    @property
    def missing_size(self) -> int:
        """Bytes of the library not in this backup.

        Returns:
            The size of the files missing.
        """
        return sum(file.size for file in self.missing)

    @property
    def to_import(self) -> tuple[MediaFile, ...]:
        """The files only in this backup that were never dealt with (0245).

        Returns:
            Them, in path order.
        """
        return proposed(self.only, self.dealt)

    @property
    def only_size(self) -> int:
        """Bytes found only in this backup.

        Returns:
            The size of its files the library lacks.
        """
        return sum(file.size for file in self.only)


@dataclass(frozen=True, slots=True)
class ComparedFiles:
    """The files compared: the library's healthy ones, and the backups' non-empty."""

    library: Sequence[MediaFile]
    backup: Sequence[MediaFile]


@dataclass(frozen=True, slots=True)
class BackupComparison:
    """The duplicate groups of the library alone, and what each backup holds."""

    groups: tuple[DuplicateGroup, ...] = ()
    folders: tuple[BackupCoverage, ...] = ()


@dataclass(frozen=True, slots=True)
class BackupFolders:
    """The backup folders of a run, in container paths."""

    folders: tuple[Path, ...] = ()

    def holding(self, path: Path) -> Path | None:
        """Tell which backup folder holds a path.

        Args:
            path: A container path.

        Returns:
            The backup folder holding it, or None when it is in the library.
        """
        return next((f for f in self.folders if is_within(path, f)), None)

    def files_in(self, files: Iterable[MediaFile]) -> tuple[MediaFile, ...]:
        """Keep the files that lie in a backup folder.

        Args:
            files: Files listed.

        Returns:
            Those of the backups.
        """
        return tuple(file for file in files if self.holding(file.path) is not None)

    def library(self, walk: Walk) -> Walk:
        """The walk without the backups: what can be cleaned, reviewed, previewed.

        Args:
            walk: Everything listed below the roots.

        Returns:
            The same walk, the media files and sidecars of the backups left out.
        """
        if not self.folders:
            return walk
        return replace(
            walk,
            files=tuple(f for f in walk.files if self.holding(f.path) is None),
            sidecars=tuple(
                s for s in walk.sidecars if self.holding(s.file.path) is None
            ),
        )

    def compare(
        self, groups: Iterable[DuplicateGroup], files: ComparedFiles
    ) -> BackupComparison:
        """Split groups of the library and the backups into what each side lacks.

        Args:
            groups: The exact duplicate groups of the library and the backups.
            files: Every file compared, on both sides.

        Returns:
            The library's groups (two copies at least) and each backup's coverage.
        """
        if not self.folders:
            return BackupComparison(groups=tuple(groups))
        kept: list[DuplicateGroup] = []
        covered: dict[Path, set[Path]] = {folder: set() for folder in self.folders}
        backed: set[Path] = set()
        for group in groups:
            mine = tuple(f for f in group.files if self.holding(f.path) is None)
            if len(mine) > 1:
                kept.append(replace(group, files=mine))
            if not mine:
                continue
            for file in group.files:
                folder = self.holding(file.path)
                if folder is not None:
                    covered[folder].update(f.path for f in mine)
                    backed.add(file.path)
        return BackupComparison(
            groups=tuple(kept),
            folders=tuple(
                BackupCoverage(
                    folder=folder,
                    files=len(theirs := self._of(folder, files.backup)),
                    missing=_sorted(
                        f for f in files.library if f.path not in covered[folder]
                    ),
                    only=_sorted(f for f in theirs if f.path not in backed),
                )
                for folder in self.folders
            ),
        )

    def _of(self, folder: Path, files: Iterable[MediaFile]) -> tuple[MediaFile, ...]:
        return tuple(file for file in files if self.holding(file.path) == folder)


def _sorted(files: Iterable[MediaFile]) -> tuple[MediaFile, ...]:
    """Order files by path, for a stable list.

    Args:
        files: Files.

    Returns:
        Them, by path.
    """
    return tuple(sorted(files, key=lambda file: str(file.path)))
