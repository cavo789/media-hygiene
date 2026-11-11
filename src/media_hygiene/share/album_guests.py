"""Which albums the devices paired as guests see (0684): a tick per album, on the PC.

Kept in `albums.json` with the album (`guests`), so it follows a rename; read back
from the disk after each change. A guest's next request reads the file again: an
album taken off the list is gone from the guest's screen at once.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.i18n import _
from media_hygiene.share.albums import AlbumsError, AlbumsFile, write_albums

if TYPE_CHECKING:
    from media_hygiene.share.album_store import AlbumStore, Shelf


def set_guests(store: AlbumStore, asked: tuple[str, bool]) -> Shelf:
    """Show an album to the guests' devices, or stop showing it.

    Args:
        store: The albums.
        asked: The album's name, and whether guests see it.

    Returns:
        The albums, read back from the disk.

    Raises:
        AlbumsError: No album of that name.
    """
    name, shown = asked
    base = store.on_disk().albums
    album = base.named(name)
    if album is None:
        raise AlbumsError(_("No album named {name}.").format(name=name))
    changed = album.model_copy(update={"guests": shown})
    albums = tuple(changed if each is album else each for each in base.albums)
    write_albums(store.place.target, AlbumsFile(albums=albums))
    return store.on_disk()


def guests_message(shelf: Shelf, name: str) -> str:
    """Say whether the guests see the album, as read back from the disk.

    Args:
        shelf: The albums, read back.
        name: The album.

    Returns:
        The sentence.
    """
    album = shelf.albums.named(name)
    if album is not None and album.guests:
        return _("The guests' devices now show {name}.").format(name=album.name)
    return _("The guests' devices no longer show {name}.").format(name=name)
