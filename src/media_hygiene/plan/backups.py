"""Backup folders: compared by content with the library, never changed (TODO 0204).

A backup folder (`--backup`, `[folders] backups`) is listed and its files are matched
with the library's by size, then partial digest (first and last 64 KiB), never read
whole (0274): a backup is only compared, a NAS read at 15 MB/s would take hours. A file
whose start and end match but whose middle differs counts as a copy: it stays in the
backup, nothing is lost. The backup's files never join the duplicate groups, so a copy
in a backup is never the reason a library file goes, and never goes itself; the near
duplicates and the burst series never see them. Two answers per backup folder: the
library's files without a copy in it (`missing`), and its files without a copy in the
library (`only`: to copy before wiping an old disk).
"""

from __future__ import annotations

from dataclasses import dataclass, field, replace
from typing import TYPE_CHECKING

from media_hygiene.paths.host_paths import is_within
from media_hygiene.plan.backup_import import DealtWith, proposed
from media_hygiene.scan.intruders import outside

if TYPE_CHECKING:
    from collections.abc import Iterable, Mapping, Sequence
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
    """The files compared: the library's healthy ones, and the backups' non-empty.

    `partials`: the partial digest of each file sharing its size with the other side
    (or with another backup file); a file left out has no copy there (0274).
    """

    library: Sequence[MediaFile]
    backup: Sequence[MediaFile]
    partials: Mapping[MediaFile, str] = field(default_factory=dict)


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
            intruders=outside(walk.intruders, self.folders),
        )

    def compare(
        self, groups: Iterable[DuplicateGroup], files: ComparedFiles
    ) -> BackupComparison:
        """Tell what each backup lacks and holds alone, by (size, partial digest).

        Args:
            groups: The exact duplicate groups of the library alone.
            files: Every file compared, on both sides, with their partial digests.

        Returns:
            The library's groups and each backup's coverage.
        """
        if not self.folders:
            return BackupComparison(groups=tuple(groups))
        library: dict[tuple[int, str], list[MediaFile]] = {}
        for file in files.library:
            if (partial := files.partials.get(file)) is not None:
                library.setdefault((file.size, partial), []).append(file)
        folders: list[BackupCoverage] = []
        for folder in self.folders:
            theirs = self._of(folder, files.backup)
            keys = {(f.size, p) for f in theirs if (p := files.partials.get(f))}
            covered = {f.path for key in keys & library.keys() for f in library[key]}
            folders.append(
                BackupCoverage(
                    folder=folder,
                    files=len(theirs),
                    missing=_sorted(f for f in files.library if f.path not in covered),
                    only=_sorted(
                        f
                        for f in theirs
                        if (f.size, files.partials.get(f, "")) not in library
                    ),
                )
            )
        return BackupComparison(groups=tuple(groups), folders=tuple(folders))

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
