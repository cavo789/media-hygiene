"""When the TV last showed an album (0603): written by the PC, read by every phone.

A phone stays read-only: the PC writes the date when the show starts. The show matters
more than the date: a file that cannot be saved (reports mounted `:ro`) leaves it
unchanged, and the show goes on.
"""

from __future__ import annotations

import datetime as dt
from typing import TYPE_CHECKING

from media_hygiene.share.albums import (
    AlbumsError,
    AlbumsFile,
    read_albums,
    write_albums,
)

if TYPE_CHECKING:
    from pathlib import Path


def note_shown(target: Path, name: str) -> None:
    """Write today's show on the album, when the file can be read and saved.

    Args:
        target: The albums file.
        name: The album's name, whatever its case.
    """
    try:
        base = read_albums(target)
        album = base.named(name)
        if album is None:
            return
        now = dt.datetime.now(tz=dt.UTC).replace(microsecond=0)
        shown = album.model_copy(update={"last_shown": now})
        albums = tuple(shown if each is album else each for each in base.albums)
        write_albums(target, AlbumsFile(albums=albums))
    except AlbumsError, OSError:
        return
