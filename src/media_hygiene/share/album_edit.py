"""Albums deleted or renamed from the albums page (0499), then read back.

Only `albums.json` changes: the photos stay where they are. A folder of links made
by `mh album` is a copy of an album at one time: it keeps its own name. The albums
of the last delete are kept next to the file (`DELETED_FILE`) for *Undo*.
"""

from __future__ import annotations

from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _, ngettext
from media_hygiene.share.album_said import cover_message
from media_hygiene.share.album_store import new_album
from media_hygiene.share.albums import (
    AlbumsError,
    AlbumsFile,
    read_albums,
    same_name,
    write_albums,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.share.album_api import AlbumAsked
    from media_hygiene.share.album_store import AlbumStore, Shelf

EDITS: Final = frozenset({"delete", "rename", "restore"})  # the albums, not files
DELETED_FILE: Final = "albums-deleted.json"  # the last delete, for Undo


def delete_albums(store: AlbumStore, names: tuple[str, ...]) -> Shelf:
    """Remove albums from the albums file; their photos stay where they are.

    Args:
        store: The albums.
        names: The albums to remove, whatever their case.

    Returns:
        The albums, read back from the disk.

    Raises:
        AlbumsError: None of the names is an album.
    """
    base = store.on_disk().albums
    gone = {same_name(name) for name in names}
    kept = tuple(album for album in base.albums if same_name(album.name) not in gone)
    if len(kept) == len(base.albums):
        raise AlbumsError(_("No album of these names: nothing deleted."))
    removed = tuple(album for album in base.albums if album not in kept)
    write_albums(_deleted(store), AlbumsFile(albums=removed))
    write_albums(store.place.target, AlbumsFile(albums=kept))
    return store.on_disk()


def restore_albums(store: AlbumStore) -> Shelf:
    """Put back the albums of the last delete (*Undo*); a name taken since stays.

    Args:
        store: The albums.

    Returns:
        The albums, read back from the disk.

    Raises:
        AlbumsError: Nothing to put back.
    """
    backup = _deleted(store)
    removed = read_albums(backup).albums
    if not removed:
        raise AlbumsError(_("No deleted album to put back."))
    base = store.on_disk().albums
    back = tuple(album for album in removed if base.named(album.name) is None)
    write_albums(store.place.target, AlbumsFile(albums=(*base.albums, *back)))
    backup.unlink(missing_ok=True)
    return store.on_disk()


def _deleted(store: AlbumStore) -> Path:
    """Where the albums of the last delete are kept: next to the albums file.

    Args:
        store: The albums.

    Returns:
        The file.
    """
    return store.place.target.with_name(DELETED_FILE)


def rename_album(store: AlbumStore, names: tuple[str, str]) -> Shelf:
    """Give an album a new name; refused when another album has it.

    Args:
        store: The albums.
        names: The album's name, then the new one as typed.

    Returns:
        The albums, read back from the disk.

    Raises:
        AlbumsError: No album of that name, a name another album has, or not a
            name an album can have.
    """
    old, typed = names
    base = store.on_disk().albums
    album = base.named(old)
    if album is None:
        raise AlbumsError(_("No album named {name}.").format(name=old))
    to = new_album(typed).name
    other = base.named(to)
    if other is not None and other is not album:
        raise AlbumsError(
            _("An album is already named {name}.").format(name=other.name)
        )
    renamed = album.model_copy(update={"name": to})
    albums = tuple(renamed if each is album else each for each in base.albums)
    write_albums(store.place.target, AlbumsFile(albums=albums))
    return store.on_disk()


def deleted_message(count: int, place: str) -> str:
    """Say how many albums were deleted, and that no photo moved.

    Args:
        count: How many, read back from the disk.
        place: The albums file, as the user sees it.

    Returns:
        The sentence.
    """
    return ngettext(
        "{count} album deleted from {place}. Your photos stay where they are.",
        "{count} albums deleted from {place}. Your photos stay where they are.",
        count,
    ).format(count=count, place=place)


def renamed_message(name: str) -> str:
    """Say the album's new name, as read back, and what keeps the old one.

    Args:
        name: The new name, read back from the disk.

    Returns:
        The sentence.
    """
    return _(
        "Renamed: {name}. A folder of links made by mh album keeps its old name."
    ).format(name=name)


def edit(store: AlbumStore, asked: AlbumAsked) -> Shelf:
    """Run a page's change of the albums themselves: delete, rename, put back.

    Args:
        store: The albums.
        asked: The request.

    Returns:
        The albums, read back from the disk.
    """
    if asked.action == "delete":
        return delete_albums(store, asked.names)
    if asked.action == "rename":
        return rename_album(store, (asked.album, asked.to))
    return restore_albums(store)


def edit_message(shelf: Shelf, asked: AlbumAsked, place: str) -> str | None:
    """Say what the albums file holds after a change, as read back from the disk.

    Args:
        shelf: The albums, read back.
        asked: The request.
        place: The albums file, as the user sees it.

    Returns:
        The sentence; None for an add or a removal (`shelf_view` says it).
    """
    if asked.action == "cover":
        return cover_message(shelf, asked.album)
    if asked.action == "delete":
        gone = sum(shelf.albums.named(name) is None for name in asked.names)
        return deleted_message(gone, place)
    if asked.action == "rename":
        return renamed_message(new_album(asked.to).name)
    if asked.action == "restore":
        return _("The deleted albums are back in {place}.").format(place=place)
    return None
