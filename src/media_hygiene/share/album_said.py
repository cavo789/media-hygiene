"""What the pages say about the albums: each one, its files, those missing (0295)."""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.console.formatting import human_number
from media_hygiene.i18n import _, ngettext

if TYPE_CHECKING:
    from media_hygiene.share.album_store import Shelf


def shelf_view(shelf: Shelf, name: str | None, place: str) -> dict[str, object]:
    """Write the albums for a page, and the sentence about the one just changed.

    Args:
        shelf: The albums, read back from the disk.
        name: The album just changed; None for the list alone.
        place: The albums file, as the user sees it.

    Returns:
        The JSON object: `albums` (name, count, missing paths), `message`.
    """
    albums = [
        {
            "name": album.name,
            "count": len(album.entries),
            "missing": list(shelf.missing.get(album.name, ())),
        }
        for album in shelf.albums.albums
    ]
    lines = [] if name is None else [album_message(shelf, name, place)]
    if name is None:
        lines.append(_list_message(len(albums), place))
    lines.extend(
        _missing_message(album.name, len(shelf.missing[album.name]))
        for album in shelf.albums.albums
        if shelf.missing.get(album.name)
    )
    return {"albums": albums, "message": " ".join(lines)}


def album_message(shelf: Shelf, name: str, place: str) -> str:
    """Say how many files an album holds, and where it is saved.

    Args:
        shelf: The albums, read back from the disk.
        name: The album.
        place: The albums file, as the user sees it.

    Returns:
        The sentence; an album left empty is said removed.
    """
    album = shelf.albums.named(name)
    if album is None:
        return _("The album {name} is empty: removed from {place}.").format(
            name=" ".join(name.split()), place=place
        )
    count = len(album.entries)
    return ngettext(
        "{name}: {count} file, saved in {place}. Only this file changed: no photo "
        "was copied or moved.",
        "{name}: {count} files, saved in {place}. Only this file changed: no photo "
        "was copied or moved.",
        count,
    ).format(name=album.name, count=human_number(count), place=place)


def _list_message(count: int, place: str) -> str:
    """Say how many albums there are.

    Args:
        count: How many.
        place: The albums file, as the user sees it.

    Returns:
        The sentence.
    """
    if not count:
        return _("No album yet: type a name, pick photos, then Add to the album.")
    return ngettext(
        "{count} album, saved in {place}.", "{count} albums, saved in {place}.", count
    ).format(count=human_number(count), place=place)


def _missing_message(name: str, count: int) -> str:
    """Say that files of an album were not found, and that they are kept.

    Args:
        name: The album.
        count: How many files are missing.

    Returns:
        The sentence.
    """
    return ngettext(
        "{count} file of {name} is missing: moved out of the folders analysed, or "
        "deleted. It stays in the album: once an audit sees it again, it comes back.",
        "{count} files of {name} are missing: moved out of the folders analysed, or "
        "deleted. They stay in the album: once an audit sees them again, they come "
        "back.",
        count,
    ).format(count=human_number(count), name=name)
