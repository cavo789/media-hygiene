"""What `slideshow` shows: a folder, the files a search finds, or the files set aside.

Read from the index alone, as `browse` and `search` do: a photo the last audit did not
see is not shown. Photos and videos (0292: a video's codec and length from what the
audit's `ffprobe` read), oldest first, the undated ones last; at most `MAX_SLIDES`,
the first ones by date.
"""

from __future__ import annotations

from dataclasses import dataclass
from pathlib import Path
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.constants import MediaKind
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.report.thumbnails import PREVIEWABLE
from media_hygiene.scan.filters import media_kind
from media_hygiene.scan.metadata import MediaMetadata
from media_hygiene.search import statements as sql
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.query import SearchQuery, parse_terms
from media_hygiene.services.search_pages import chosen_desk
from media_hygiene.slideshow.slides import Film, Slide

if TYPE_CHECKING:
    import sqlite3
    from collections.abc import Iterable

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

# The phone shows a thumbnail of each photo: a holiday is a few hundred photos.
MAX_SLIDES: Final = 3000
_AFTER_SLASH: Final = "0"  # the character after `/`: ends the range of a folder
_BY_PATH: Final = f"SELECT rowid, path, {DAY}(media_date) FROM files WHERE path = ?"  # noqa: S608
_METADATA: Final = "SELECT metadata FROM files WHERE rowid = ?"
_SHOWN: Final = PREVIEWABLE | {MediaKind.VIDEO}


@dataclass(frozen=True, slots=True)
class Pick:
    """What the command was asked to show: one of the three."""

    folder: str | None = None  # as the Explorer shows it
    words: str | None = None  # a search, as typed in `search`
    chosen: bool = False  # the files set aside in `search` or `browse`


@dataclass(frozen=True, slots=True)
class Picked:
    """The photos of the show, and how many were found before the cut."""

    slides: tuple[Slide, ...]
    found: int


def picked_slides(runtime: Runtime, search: SearchIndex, pick: Pick) -> Picked:
    """List the photos of the show, oldest first.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        pick: The folder, the words, or the files set aside.

    Returns:
        The photos, at most `MAX_SLIDES`.

    Raises:
        MediaHygieneError: None or more than one of the three was given.
    """
    given = sum((pick.folder is not None, pick.words is not None, pick.chosen))
    if given != 1:
        raise MediaHygieneError(
            _(
                'Say what to show, one of: --folder "C:\\Photos\\Holidays", --search '
                '"words", or --chosen (the files set aside).'
            )
        )
    connection = search.connection
    if pick.folder is not None:
        folder = runtime.mapper.to_container(pick.folder)
        bounds = (f"{folder}/", f"{folder}{_AFTER_SLASH}")
        rows: Iterable[tuple[int, str, str | None]] = (
            (key, path, day)
            for key, path, _size, day in connection.execute(sql.FOLDER_FILES, bounds)
        )
    elif pick.words is not None:
        found = search.find(SearchQuery(parse_terms(pick.words)), MAX_SLIDES)
        rows = ((hit.key, str(hit.photo.path), hit.date) for hit in found.hits)
    else:
        paths = sorted(chosen_desk(runtime, search).paths())
        rows = (
            row
            for path in paths
            for row in connection.execute(
                _BY_PATH, (str(runtime.mapper.to_container(path)),)
            )
        )
    photos = sorted(
        (
            (day is None, day or "", path.casefold(), key, Path(path))
            for key, path, day in rows
            if media_kind(Path(path)) in _SHOWN
        ),
    )
    slides = tuple(
        Slide(key, day or None, _film(connection, key, source))
        for _undated, day, _path, key, source in photos[:MAX_SLIDES]
    )
    return Picked(slides, len(photos))


def _film(connection: sqlite3.Connection, key: int, source: Path) -> Film | None:
    """What the index knows of a video: its codec and its length.

    Args:
        connection: The open index.
        key: The file's key.
        source: The file.

    Returns:
        The video's facts; None for a photo.
    """
    if media_kind(source) is not MediaKind.VIDEO:
        return None
    row = connection.execute(_METADATA, (key,)).fetchone()
    metadata = MediaMetadata()
    if row is not None and isinstance(row[0], str):
        try:
            metadata = MediaMetadata.model_validate_json(row[0])
        except ValidationError:
            metadata = MediaMetadata()
    return Film(source.suffix.lower(), metadata.codec, metadata.duration)
