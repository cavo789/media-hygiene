"""What `slideshow` shows: a folder, the files a search finds, or an album (0295).

Read from the index alone, as `browse` and `search` do: a photo the last audit did not
see is not shown. Photos and videos (0292: a video's codec and length from what the
audit's `ffprobe` read), oldest first, the undated ones last; at most `MAX_SLIDES`,
the first ones by date. An album's files are followed if they moved
(`share.album_follow`); those missing are counted, never shown.
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
from media_hygiene.services.albums import album_store
from media_hygiene.services.slideshow_notes import notes_of
from media_hygiene.services.slideshow_story import told_slides
from media_hygiene.share.albums import AlbumsError
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
    """What the command was asked to show: one of the four."""

    folder: str | None = None  # as the Explorer shows it
    words: str | None = None  # a search, as typed in `search`
    album: str | None = None  # an album's name (`albums.json`)
    files: tuple[Path, ...] | None = None  # picked on a page, in the container (0454)


@dataclass(frozen=True, slots=True)
class Picked:
    """The photos of the show, and how many were found before the cut."""

    slides: tuple[Slide, ...]
    found: int
    missing: int = 0  # files of the album found nowhere


def picked_slides(runtime: Runtime, search: SearchIndex, pick: Pick) -> Picked:
    """List the photos of the show, oldest first.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        pick: The folder, the words, or the album.

    Returns:
        The photos, at most `MAX_SLIDES`.

    Raises:
        MediaHygieneError: None or more than one of the three was given, or no
            album has that name.
    """
    given = (pick.folder, pick.words, pick.album, pick.files)
    if sum(each is not None for each in given) != 1:
        raise MediaHygieneError(
            _(
                'Say what to show, one of: --folder "C:\\Photos\\Holidays", --search '
                '"words", or --album "Crete 2023".'
            )
        )
    missing = 0
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
        if pick.files is None:
            paths, missing = album_paths(runtime, pick.album or "")
            inside = [runtime.mapper.to_container(path) for path in paths]
        else:
            inside = list(pick.files)
        rows = (
            row for path in inside for row in connection.execute(_BY_PATH, (str(path),))
        )
    photos = sorted(
        (
            (day is None, day or "", path.casefold(), key, Path(path))
            for key, path, day in rows
            if media_kind(Path(path)) in _SHOWN
        ),
    )
    slides = told_slides(
        runtime,
        connection,
        [
            (
                Slide(
                    key,
                    day or None,
                    _film(connection, key, source),
                    notes=notes_of(connection, key, source),
                ),
                source,
            )
            for _undated, day, _path, key, source in photos[:MAX_SLIDES]
        ],
    )
    return Picked(slides, len(photos), missing)


def album_paths(runtime: Runtime, name: str) -> tuple[list[str], int]:
    """The host paths of an album's files found on the disk, and how many are not.

    Args:
        runtime: Settings, mount points and output.
        name: The album's name.

    Returns:
        The paths, and the count of files missing.

    Raises:
        AlbumsError: No album of that name, or no albums file.
    """
    shelf = album_store(runtime).on_disk()
    album = shelf.albums.named(name)
    if album is None:
        names = ", ".join(each.name for each in shelf.albums.albums) or "-"
        raise AlbumsError(
            _("No album named {name}. The albums: {names}.").format(
                name=name, names=names
            ),
            _("Add photos to an album in search or browse."),
        )
    gone = frozenset(shelf.missing.get(album.name, ()))
    paths = sorted(entry.path for entry in album.entries if entry.path not in gone)
    return paths, len(gone)


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
