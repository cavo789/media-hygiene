"""What the Events tab says of one event made from the index (0572, 0574).

`card_of` writes one event of `span_events` for the list: its id (`<first>..<last>`),
its days, its count, the folders it lies in and whether the user chose not to sort it
(`left`: every file's content id in `events/left.toml`, `span_left`).
"""

from __future__ import annotations

from datetime import datetime
from pathlib import Path, PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.dates import exif_datetime

if TYPE_CHECKING:
    from collections.abc import Sequence

    from media_hygiene.paths.host_paths import HostPathMapper

BETWEEN: Final = ".."
_ISO_LENGTH: Final = 19  # `2019-06-12T14:30:12`, the zone dropped
_FOLDERS_SHOWN: Final = 3

# key, path, size, mtime, day, date as written, content id (None before hashing)
type Row = tuple[int, str, int, int, str, str, str | None]


def when_taken(row: Row) -> datetime:
    """When a file was taken: its date as written, else its day at midnight.

    Args:
        row: Its row.

    Returns:
        The naive local time.
    """
    written = exif_datetime(row[5])
    if written is not None:
        return written
    try:
        return datetime.fromisoformat(row[5][:_ISO_LENGTH])
    except ValueError:
        return datetime.fromisoformat(row[4])


def ids_of(rows: Sequence[Row]) -> frozenset[str]:
    """The content ids of an event's files.

    Args:
        rows: Its rows.

    Returns:
        Those known: a file not hashed yet has none.
    """
    return frozenset(row[6] for row in rows if row[6])


def card_of(
    group: Sequence[tuple[datetime, Row]],
    mapper: HostPathMapper,
    left: frozenset[str],
) -> dict[str, object]:
    """What the list says of one event.

    Args:
        group: Its files, in the order taken.
        mapper: Writes the folders as the user knows them.
        left: The content ids of the events the user chose not to sort.

    Returns:
        `{id, first, last, files, folders, more_folders, left}`.
    """
    first, last = group[0][0].isoformat(), group[-1][0].isoformat()
    parents = dict.fromkeys(PurePosixPath(row[1]).parent for _when_, row in group)
    folders = [mapper.to_host(Path(parent)) for parent in parents]
    ids = ids_of([row for _when_, row in group])
    return {
        "id": f"{first}{BETWEEN}{last}",
        "first": first,
        "last": last,
        "files": len(group),
        "folders": list(folders)[:_FOLDERS_SHOWN],
        "more_folders": max(0, len(folders) - _FOLDERS_SHOWN),
        "left": bool(ids) and ids <= left,
    }
