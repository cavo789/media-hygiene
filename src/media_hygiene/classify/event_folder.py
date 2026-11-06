"""Find an event's folder again when the user renamed it in Explorer (0556).

No list of files is stored: an event's files are those of its folder
`YYYY/YYYY-MM/<name>`. Renamed, the folder is found again from the index: the folder
holding most of the files of the event's days and cameras. None found: the page asks.
"""

from __future__ import annotations

from collections import Counter
from pathlib import PurePosixPath
from typing import TYPE_CHECKING, Final

from media_hygiene.classify.found_folders import moment
from media_hygiene.classify.hand_days import SIDECAR_DAY, known, ready
from media_hygiene.classify.rules.calendar import parse_one_off

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.config.classify_rules import ClassifyRule

_DATED: Final = f"SELECT path, media_date, camera, {SIDECAR_DAY} FROM files"  # noqa: S608


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
    cameras = {device.casefold() for device in rule.devices}
    folders: Counter[str] = Counter()
    for path, written, camera, hand in ready(connection).execute(_DATED):
        when = known(moment(written) if written else None, hand and moment(hand))
        if when is None or not period.contains(when.date()):
            continue
        if cameras and str(camera or "").strip().casefold() not in cameras:
            continue
        folders[str(PurePosixPath(path).parent)] += 1
    if expected in folders:
        return expected
    return folders.most_common(1)[0][0] if folders else None
