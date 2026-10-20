"""The report's section of the backup folders, and its two CSV files (TODO 0204).

Per backup folder: the library's files without an identical copy in it, and its files
without an identical copy in the library. The page lists the first ones of each, host
paths; `backup-missing.csv` and `backup-only.csv`, next to `plan.csv`, list them all.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.report.csv_export import (
    CSV_DATE_FORMAT,
    CSV_ENCODING,
    list_separator,
    spreadsheet_text,
)

if TYPE_CHECKING:
    from collections.abc import Sequence
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.plan.backups import BackupCoverage
    from media_hygiene.scan.models import MediaFile

MISSING_CSV_FILE_NAME: Final = "backup-missing.csv"
ONLY_CSV_FILE_NAME: Final = "backup-only.csv"
# The files of each list shown in the page; the CSV files list them all.
MAX_BACKUP_FILES_IN_REPORT: Final = 200
_NANOSECONDS: Final = 1_000_000_000


@dataclass(frozen=True, slots=True)
class BackupList:
    """One list of a backup folder: the first files, how many, their size."""

    paths: tuple[str, ...] = ()
    count: int = 0
    size: int = 0

    @property
    def hidden(self) -> int:
        """How many files the page does not show.

        Returns:
            Those beyond the first ones.
        """
        return self.count - len(self.paths)


@dataclass(frozen=True, slots=True)
class BackupView:
    """One backup folder: what it lacks, what only it holds."""

    folder: str
    files: int
    missing: BackupList
    only: BackupList


def backup_section(
    backups: Sequence[BackupCoverage], mapper: HostPathMapper
) -> tuple[BackupView, ...]:
    """Describe every backup folder compared, in host paths.

    Args:
        backups: Each backup folder compared with the library.
        mapper: Host/container path translator.

    Returns:
        One view per backup folder.
    """
    return tuple(
        BackupView(
            folder=mapper.to_host(backup.folder),
            files=backup.files,
            missing=_listed(backup.missing, mapper),
            only=_listed(backup.only, mapper),
        )
        for backup in backups
    )


def backup_only(backups: Sequence[BackupCoverage]) -> int:
    """Count the files only a backup holds that `import` would copy back.

    Args:
        backups: Each backup folder compared with the library.

    Returns:
        The files never imported nor dealt with, in every backup.
    """
    return sum(len(backup.to_import) for backup in backups)


def write_backup_csvs(
    folder: Path, backups: Sequence[BackupCoverage], mapper: HostPathMapper
) -> None:
    """Write `backup-missing.csv` and `backup-only.csv`, when a backup was compared.

    Args:
        folder: The report folder.
        backups: Each backup folder compared with the library.
        mapper: Host/container path translator.
    """
    if not backups:
        return
    lists = {
        MISSING_CSV_FILE_NAME: [(b.folder, f) for b in backups for f in b.missing],
        ONLY_CSV_FILE_NAME: [(b.folder, f) for b in backups for f in b.only],
    }
    for name, rows in lists.items():
        with (folder / name).open("w", encoding=CSV_ENCODING, newline="") as stream:
            writer = csv.writer(stream, delimiter=list_separator())
            writer.writerow(
                (
                    _("Backup folder"),
                    _("File"),
                    _("Folder"),
                    _("Size (bytes)"),
                    _("Modified (UTC)"),
                )
            )
            writer.writerows(_row(backup, file, mapper) for backup, file in rows)


def _row(backup: Path, file: MediaFile, mapper: HostPathMapper) -> tuple[str, ...]:
    """One CSV row: the backup folder, then the file.

    Args:
        backup: The backup folder the row is about.
        file: The file.
        mapper: Host/container path translator.

    Returns:
        The row, in host paths.
    """
    modified = datetime.fromtimestamp(file.mtime_ns / _NANOSECONDS, UTC)
    texts = (
        mapper.to_host(backup),
        mapper.to_host(file.path),
        mapper.to_host(file.path.parent),
        str(file.size),
        modified.strftime(CSV_DATE_FORMAT),
    )
    return tuple(spreadsheet_text(text) for text in texts)


def _listed(files: Sequence[MediaFile], mapper: HostPathMapper) -> BackupList:
    """The first files of a list, in host paths, with the count and size of all.

    Args:
        files: The files of the list.
        mapper: Host/container path translator.

    Returns:
        The list as the page shows it.
    """
    return BackupList(
        paths=tuple(mapper.to_host(f.path) for f in files[:MAX_BACKUP_FILES_IN_REPORT]),
        count=len(files),
        size=sum(file.size for file in files),
    )
