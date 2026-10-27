"""Add files to an album or take them out, saved at once, then read back (0295).

What a page shows is what the file holds, never what was meant to be saved: each
change is written, then the file is read again, its moved entries followed
(`album_follow`) and saved again when a path changed. Only `albums.json` is written:
no photo is copied, moved or touched.
"""

from __future__ import annotations

import datetime as dt
from dataclasses import dataclass
from typing import TYPE_CHECKING

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.share.album_cover import followed_cover
from media_hygiene.share.album_follow import digest_of, follow, index_of
from media_hygiene.share.albums import (
    MAX_NAME,
    Album,
    AlbumEntry,
    AlbumsError,
    AlbumsFile,
    read_albums,
    write_albums,
)

if TYPE_CHECKING:
    from collections.abc import Mapping
    from pathlib import Path

    from media_hygiene.share.album_follow import Lookup


@dataclass(frozen=True, slots=True)
class AlbumsPlace:
    """The albums file: in the container, and as the user sees it."""

    target: Path
    host: str


@dataclass(frozen=True, slots=True)
class Shelf:
    """The albums as read back from the disk, and the files missing from each."""

    albums: AlbumsFile
    missing: Mapping[str, tuple[str, ...]]  # host paths, by album name


@dataclass(frozen=True, slots=True)
class AlbumChange:
    """Files to add to an album, or to take out of it."""

    name: str
    files: tuple[Path, ...]  # in the container


class AlbumStore:
    """The albums of `albums.json`: read, followed, changed."""

    def __init__(self, place: AlbumsPlace, lookup: Lookup) -> None:
        """Work on one albums file.

        Args:
            place: The file.
            lookup: The index (to follow moved files) and the mapper.
        """
        self.place = place
        self.lookup = lookup

    def on_disk(self) -> Shelf:
        """Read the albums, follow the files that moved, save what was found again.

        Returns:
            The albums, read back from the disk.

        Raises:
            AlbumsError: The file is not an albums file.
            OSError: A path found again cannot be saved.
        """
        base = read_albums(self.place.target)
        albums: list[Album] = []
        missing: dict[str, tuple[str, ...]] = {}
        changed = False
        for album in base.albums:
            followed = follow(album.entries, self.lookup)
            cover = followed_cover(album, self.lookup)  # 0371
            update = {"entries": followed.entries, "cover": cover}
            albums.append(album.model_copy(update=update))
            missing[album.name] = followed.missing
            changed = changed or followed.changed or cover != album.cover
        if not changed:
            return Shelf(base, missing)
        write_albums(self.place.target, AlbumsFile(albums=tuple(albums)))
        return Shelf(read_albums(self.place.target), missing)

    def add(self, change: AlbumChange) -> Shelf:
        """Add files to an album, created when new; a file already in it stays once.

        Args:
            change: The album's name and the files.

        Returns:
            The albums, read back from the disk.

        Raises:
            AlbumsError: The name is not one an album can have, or the file is not
                an albums file.
            OSError: A file cannot be read, or the albums cannot be saved.
        """
        base = read_albums(self.place.target)
        album = base.named(change.name) or _new_album(change.name)
        known = {entry.path for entry in album.entries}
        added = dt.datetime.now(tz=dt.UTC).replace(microsecond=0)
        entries = list(album.entries)
        mapper = self.lookup.mapper
        with index_of(self.lookup) as connection:
            for source in change.files:
                host = mapper.to_host(source)
                if host in known:
                    continue
                known.add(host)
                size = source.stat().st_size
                digest = digest_of(connection, source)
                entries.append(
                    AlbumEntry(path=host, sha256=digest, size=size, added=added)
                )
        return self._save(base, album.model_copy(update={"entries": tuple(entries)}))

    def remove(self, change: AlbumChange) -> Shelf:
        """Take files out of an album; an album left empty is removed.

        Args:
            change: The album's name and the files.

        Returns:
            The albums, read back from the disk.

        Raises:
            AlbumsError: No album of that name, or the file is not an albums file.
            OSError: The albums cannot be saved.
        """
        base = read_albums(self.place.target)
        album = base.named(change.name)
        if album is None:
            raise AlbumsError(_("No album named {name}.").format(name=change.name))
        gone = {self.lookup.mapper.to_host(source) for source in change.files}
        kept = tuple(entry for entry in album.entries if entry.path not in gone)
        return self._save(base, album.model_copy(update={"entries": kept}))

    def _save(self, base: AlbumsFile, album: Album) -> Shelf:
        """Write the albums with one album changed (gone when empty), then read back.

        Args:
            base: The albums as read before the change.
            album: The album, changed.

        Returns:
            The albums, read back from the disk.
        """
        names = [a.name for a in base.albums]
        if album.name in names:
            at = names.index(album.name)
            ordered = (*base.albums[:at], album, *base.albums[at + 1 :])
        else:
            ordered = (*base.albums, album)
        albums = tuple(a for a in ordered if a.entries)
        write_albums(self.place.target, AlbumsFile(albums=albums))
        return self.on_disk()


def _new_album(name: str) -> Album:
    """An album not saved yet, its name with single spaces.

    Args:
        name: As typed.

    Returns:
        It, empty.

    Raises:
        AlbumsError: The name is empty, too long, or holds a double quote.
    """
    try:
        return Album(name=" ".join(name.split()))
    except ValidationError as exc:
        message = _(
            "An album's name: 1 to {most} characters, without double quotes."
        ).format(most=MAX_NAME)
        raise AlbumsError(message) from exc
