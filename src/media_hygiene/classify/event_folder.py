"""Find an event's folder again when the user renamed it in Explorer (0556).

No list of files is stored: an event's files are those of its folder
`YYYY/YYYY-MM/<name>`. Renamed, the folder is found again from the index: the folder
holding most of the files of the event's days and cameras. None found: the page asks.
"""

from __future__ import annotations

from collections import Counter
from datetime import date
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.rules.calendar import parse_one_off

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.config.classify_rules import ClassifyRule

_DATED: Final = (
    "SELECT path, media_date, camera FROM files WHERE media_date IS NOT NULL"
)
_DAY: Final = slice(0, 10)  # `YYYY:MM:DD` (EXIF) or `YYYY-MM-DD` (a video, ISO)


def event_folder(
    connection: sqlite3.Connection, rule: ClassifyRule, expected: str
) -> str | None:
    """The event's folder: where it was put, else where its files are now.

    Args:
        connection: The index.
        rule: The event: its days and cameras.
        expected: Its folder as the move wrote it (container path).

    Returns:
        The folder; None when no indexed file of its days and cameras is found.
    """
    period = parse_one_off(rule.dates)
    known = {device.casefold() for device in rule.devices}
    folders: Counter[str] = Counter()
    for path, written, camera in connection.execute(_DATED):
        try:
            day = date.fromisoformat(str(written)[_DAY].replace(":", "-"))
        except ValueError:
            continue
        if not period.contains(day):
            continue
        if known and str(camera or "").strip().casefold() not in known:
            continue
        folders[str(PurePosixPath(path).parent)] += 1
    if expected in folders:
        return expected
    return folders.most_common(1)[0][0] if folders else None
