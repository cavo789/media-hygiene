"""The report's section of intruder files, and `intruders.csv` (TODO 0410).

Files of the photo folders that are neither photos, videos nor companions (a zip, a
docx, a pdf): totals per extension, the heaviest folders, and every file in
`intruders.csv`, next to `plan.csv`. Nothing is moved: the user chooses.
"""

from __future__ import annotations

import csv
from dataclasses import dataclass
from datetime import UTC, datetime
from pathlib import Path
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.report.csv_export import (
    CSV_DATE_FORMAT,
    CSV_ENCODING,
    list_separator,
    spreadsheet_text,
)
from media_hygiene.scan.intruders import tally

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.scan.intruders import Intruder

INTRUDERS_CSV_FILE_NAME: Final = "intruders.csv"
# The extensions and folders the page lists, the heaviest first; the CSV lists all.
MAX_INTRUDER_ROWS: Final = 20
_NANOSECONDS: Final = 1_000_000_000


@dataclass(frozen=True, slots=True)
class IntruderRow:
    """One line of the section: an extension or a folder, its files, their bytes."""

    name: str
    count: int
    size: int


@dataclass(frozen=True, slots=True)
class IntruderSection:
    """The section: totals, per extension, the heaviest folders."""

    count: int
    size: int
    extensions: tuple[IntruderRow, ...]
    folders: tuple[IntruderRow, ...]
    hidden_folders: int


def intruder_section(
    intruders: Sequence[Intruder], mapper: HostPathMapper
) -> IntruderSection | None:
    """The section of the report, or None when every file is a photo or a video.

    Args:
        intruders: The intruder files the audit found.
        mapper: Host/container path translator.

    Returns:
        The totals and the heaviest extensions and folders, in host paths.
    """
    if not intruders:
        return None
    by_folder = tally(intruders, by_folder=True)
    folders = tuple(
        IntruderRow(mapper.to_host(Path(key)), count, size)
        for key, count, size in by_folder.heaviest(MAX_INTRUDER_ROWS)
    )
    return IntruderSection(
        count=len(intruders),
        size=sum(item.size for item in intruders),
        extensions=tuple(
            IntruderRow(key, count, size)
            for key, count, size in tally(intruders).heaviest(MAX_INTRUDER_ROWS)
        ),
        folders=folders,
        hidden_folders=len(by_folder.count) - len(folders),
    )


def write_intruders_csv(
    folder: Path, intruders: Sequence[Intruder], mapper: HostPathMapper
) -> None:
    """Write `intruders.csv`, one row per file, when there is one.

    Args:
        folder: The report folder.
        intruders: The intruder files.
        mapper: Host/container path translator.
    """
    if not intruders:
        return
    target = folder / INTRUDERS_CSV_FILE_NAME
    with target.open("w", encoding=CSV_ENCODING, newline="") as stream:
        writer = csv.writer(stream, delimiter=list_separator())
        writer.writerow(
            (
                _("File"),
                _("Folder"),
                _("Extension"),
                _("Size (bytes)"),
                _("Modified (UTC)"),
            )
        )
        ordered = sorted(intruders, key=lambda item: item.path)
        writer.writerows(_row(item, mapper) for item in ordered)


def _row(item: Intruder, mapper: HostPathMapper) -> tuple[str, ...]:
    """One CSV row, in host paths.

    Args:
        item: The file.
        mapper: Host/container path translator.

    Returns:
        The row.
    """
    modified = datetime.fromtimestamp(item.mtime_ns / _NANOSECONDS, UTC)
    texts = (
        mapper.to_host(item.path),
        mapper.to_host(item.path.parent),
        item.extension,
        str(item.size),
        modified.strftime(CSV_DATE_FORMAT),
    )
    return tuple(spreadsheet_text(text) for text in texts)
