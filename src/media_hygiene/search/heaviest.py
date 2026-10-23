"""The heaviest files of the whole library, for `browse`: where the space goes.

`POST /api/heaviest` lists the files of every mounted folder, the largest first or,
for videos, the highest bit rate first (the clips worst compressed for their length,
those worth lightening), the photos or videos only. One pass over the index, in that
order: the files outside the mounted folders are skipped, the total of the library
counted on the way; the metadata is read only for the files listed.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from itertools import batched
from pathlib import Path
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.console.formatting import human_size
from media_hygiene.i18n import _, ngettext
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.folder_order import (
    Shown,  # pydantic reads it
    is_shown,
)

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.search.folder_order import FileRow

HEAVIEST_PATH: Final = "/api/heaviest"
FIRST_SHOWN: Final = 200  # the page asks for more, by as many, with *Show more*
_MOST: Final = 20_000
_FROM: Final = f"SELECT rowid, path, size, {DAY}(media_date), {{rate}} FROM files"  # noqa: S608
_BY_SIZE: Final = _FROM.format(rate="NULL") + " ORDER BY size DESC, path"
_RATE: Final = "json_extract(metadata, '$.bit_rate')"
# A file whose bit rate is unknown (a photo, a video the audit could not read) last.
_BY_RATE: Final = (
    _FROM.format(rate=_RATE) + f" ORDER BY {_RATE} IS NULL, {_RATE} DESC, path"
)
_METADATA: Final = "SELECT rowid, metadata FROM files WHERE rowid IN ({marks})"
_BATCH: Final = 500  # rowids per query: far under SQLite's limit of parameters
_MINUTE: Final = 60
_HOUR: Final = 3_600
_MEGA: Final = 1_000_000
_BY: Final = "\N{MULTIPLICATION SIGN}"  # between the width and the height


class HeaviestAsked(BaseModel):
    """`POST /api/heaviest`: the kind shown, the order, how many."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    kind: Shown = "videos"
    order: Literal["size", "rate"] = "size"
    limit: int = Field(default=FIRST_SHOWN, ge=1, le=_MOST)


@dataclass(frozen=True, slots=True)
class Heaviest:
    """The files listed, the metadata of each, and the size of the whole library."""

    rows: tuple[FileRow, ...]
    metadata: dict[int, dict[str, object]]
    library: int


def heaviest(
    connection: sqlite3.Connection, asked: HeaviestAsked, roots: tuple[Path, ...]
) -> Heaviest:
    """Find the heaviest files under the mounted folders.

    Args:
        connection: The index, read-only.
        asked: The kind, order and number of files.
        roots: The mounted folders, in the container.

    Returns:
        The files in order, at most `limit`, and the bytes of every file under roots.
    """
    rows: list[FileRow] = []
    library = 0
    query = _BY_RATE if asked.order == "rate" else _BY_SIZE
    for key, text, size, day, _rate in connection.execute(query):
        path = Path(text)
        if not any(path.is_relative_to(root) for root in roots):
            continue
        library += size
        if len(rows) < asked.limit and is_shown(path, asked.kind):
            rows.append((key, text, size, day))
    return Heaviest(tuple(rows), _metadata(connection, rows), library)


def _metadata(
    connection: sqlite3.Connection, rows: list[FileRow]
) -> dict[int, dict[str, object]]:
    """Read the metadata of the files listed only.

    Args:
        connection: The index.
        rows: The files listed.

    Returns:
        Each file's metadata, by key; a file without any is left out.
    """
    found: dict[int, dict[str, object]] = {}
    for keys in batched((row[0] for row in rows), _BATCH, strict=False):
        query = _METADATA.format(marks=", ".join("?" * len(keys)))
        for key, text in connection.execute(query, keys):
            if text:
                found[key] = json.loads(text)
    return found


def video_facts(metadata: dict[str, object]) -> str:
    """Say what a video is, for its tile: `12 min · 12.7 Mb/s · mjpeg · 1280 by 720`.

    Args:
        metadata: Its metadata (`MediaMetadata` as stored).

    Returns:
        The facts known, joined; empty when none is.
    """
    duration, rate = metadata.get("duration"), metadata.get("bit_rate")
    width, height = metadata.get("width"), metadata.get("height")
    facts = [
        _duration(duration) if isinstance(duration, int | float) else "",
        _("{n} Mb/s").format(n=f"{rate / _MEGA:.1f}") if isinstance(rate, int) else "",
        str(metadata.get("codec") or ""),
        f"{width}{_BY}{height}" if width and height else "",
    ]
    return " · ".join(fact for fact in facts if fact)


def _duration(seconds: float) -> str:
    """Say how long a video lasts, roughly.

    Args:
        seconds: Its length.

    Returns:
        `45 s`, `12 min` or `1 h 05`.
    """
    whole = round(seconds)
    if whole < _MINUTE:
        return _("{n} s").format(n=whole)
    if whole < _HOUR:
        return _("{n} min").format(n=round(whole / _MINUTE))
    hours, rest = divmod(whole, _HOUR)
    return _("{h} h {m}").format(h=hours, m=f"{rest // _MINUTE:02d}")


def listed_total(found: Heaviest) -> str:
    """Say what the list holds: `200 files, 61.4 GB, 25 % of your library`.

    Args:
        found: The files listed.

    Returns:
        The sentence of the bar above the grid.
    """
    count = len(found.rows)
    size = sum(row[2] for row in found.rows)
    share = round(100 * size / found.library) if found.library else 0
    sentence = ngettext(
        "{n} file, {size}, {share} of your library",
        "{n} files, {size}, {share} of your library",
        count,
    )
    return sentence.format(n=count, size=human_size(size), share=f"{share} %")
