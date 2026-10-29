"""The end of the chain after a phone import (0475): place names, then the slideshow.

`mh` runs the steps of `[imports] then` once the copies are done (`audit`, 🤖 `tags`);
`phone-end` comes last: it offers the new spots' names online when `places` is on (its
own question, 0474), then proposes the new photos' name (0477) and the slideshow.
The new files are those of the import's folder in its period: the same rules as the
copy (the day in the name, else the modified time).
"""

from __future__ import annotations

import sqlite3
from datetime import UTC, datetime
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import MEDIA_EXTENSIONS
from media_hygiene.search.event_suggest import title_of
from media_hygiene.services.import_since import (
    file_day,
    first_day,
    kept,
    last_import,
    today_local,
)

if TYPE_CHECKING:
    from datetime import date
    from pathlib import Path

    from media_hygiene.services.runtime import Runtime

# The hidden command `mh` runs at the end of `import --phone`'s chain.
PHONE_END: Final = "phone-end"


def new_files(folder: Path, first: date | None) -> tuple[Path, ...]:
    """The photos and videos of the import's folder in its period.

    Args:
        folder: Where the import copied (container path).
        first: The first day of the period; None: every file.

    Returns:
        Their paths, sorted.
    """
    found = []
    for path in folder.rglob("*"):
        if path.suffix.casefold() not in MEDIA_EXTENSIONS or not path.is_file():
            continue
        if kept(path.name, _stamp(path), first):
            found.append(path)
    return tuple(sorted(found))


def imported(runtime: Runtime, folder: str, since: str | None) -> tuple[Path, ...]:
    """The files of an import: its folder as the Explorer shows it, in its period.

    Args:
        runtime: Mount points (the journal holds the last import's day).
        folder: The host folder the import copied into.
        since: `--since`: today, week, month, all, a day; None: since the last import.

    Returns:
        Their container paths, sorted.
    """
    first = first_day(since, today_local(), last_import(runtime.locations.journal_dir))
    return new_files(runtime.mapper.to_container(folder), first)


def show_title(runtime: Runtime, files: tuple[Path, ...]) -> str:
    """The name proposed for the new photos, from the index's tags.

    Args:
        runtime: Settings and mount points (the index).
        files: The new files.

    Returns:
        « Walk in Liège », the place and the day, or the day; empty without files.
    """
    index = runtime.index_file
    if not files or index is None or not index.is_file():
        return ""
    days = sorted(
        day for path in files if (day := file_day(path.name, _stamp(path))) is not None
    )
    connection = sqlite3.connect(f"file:{index}?mode=ro", uri=True)
    try:
        return title_of(
            connection, [str(path) for path in files], days[0] if days else None
        )
    finally:
        connection.close()


def _stamp(path: Path) -> str:
    """A file's modified time, ISO, UTC.

    Args:
        path: The file.

    Returns:
        It.
    """
    return datetime.fromtimestamp(path.stat().st_mtime, UTC).isoformat()
