"""An album's cover chosen by the user (0371): saved, read back, found by key.

The cover names its photo by path, SHA-256 and size, as the album's entry does: when
the file moves, the entry is followed (`AlbumStore.on_disk`), and the cover's path with
it, so two identical copies of one album stay apart. A cover whose photo was taken out
of the album, or is found nowhere, gives way to the tool's choice, silently.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.share.album_follow import follow
from media_hygiene.share.albums import (
    AlbumCover,
    AlbumEntry,
    AlbumsError,
    AlbumsFile,
    read_albums,
    write_albums,
)

if TYPE_CHECKING:
    import sqlite3

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.share.album_follow import Lookup
    from media_hygiene.share.album_store import AlbumChange, AlbumStore, Shelf
    from media_hygiene.share.albums import Album

_KEY: Final = "SELECT rowid FROM files WHERE path = ?"
_SINCE: Final = dt.datetime.min.replace(tzinfo=dt.UTC)  # an entry's date, unused here


def choose_cover(store: AlbumStore, change: AlbumChange) -> Shelf:
    """Make a file of an album its cover; save, then read back.

    Args:
        store: The albums.
        change: The album's name and one file, in the container.

    Returns:
        The albums, read back from the disk.

    Raises:
        AlbumsError: No album of that name, or the file is not in it.
        OSError: The albums cannot be saved.
    """
    base = read_albums(store.place.target)
    album = base.named(change.name)
    if album is None:
        raise AlbumsError(_("No album named {name}.").format(name=change.name))
    hosts = {store.lookup.mapper.to_host(source) for source in change.files}
    entry = next((each for each in album.entries if each.path in hosts), None)
    if entry is None or len(change.files) != 1:
        raise AlbumsError(_("Only a photo of the album can be its cover."))
    cover = AlbumCover(path=entry.path, sha256=entry.sha256, size=entry.size)
    chosen = album.model_copy(update={"cover": cover})
    albums = tuple(chosen if each is album else each for each in base.albums)
    write_albums(store.place.target, AlbumsFile(albums=albums))
    return store.on_disk()


def followed_cover(album: Album, lookup: Lookup) -> AlbumCover | None:
    """The chosen cover, its path followed like an entry's when its file moved.

    Args:
        album: The album, as read.
        lookup: The index and the mapper.

    Returns:
        The cover, at the path its file has now (unchanged when not found).
    """
    cover = album.cover
    if cover is None or lookup.mapper.to_container(cover.path).is_file():
        return cover
    entry = AlbumEntry(
        path=cover.path, sha256=cover.sha256, size=cover.size, added=_SINCE
    )
    found = follow((entry,), lookup).entries[0].path
    return cover if found == cover.path else cover.model_copy(update={"path": found})


def cover_key(
    connection: sqlite3.Connection, album: Album, mapper: HostPathMapper
) -> int | None:
    """The index key of the cover the user chose, where its entry is now.

    Args:
        connection: The open index.
        album: The album, its moved entries followed.
        mapper: Host paths to container paths.

    Returns:
        The key; None without a chosen cover, or one no longer found.
    """
    entry = album.cover_entry()
    if entry is None:
        return None
    row = connection.execute(_KEY, (str(mapper.to_container(entry.path)),)).fetchone()
    return None if row is None else int(row[0])
