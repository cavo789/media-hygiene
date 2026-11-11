"""The albums API of a page whose keys are its own (0657): the phone page, `/person`.

A tile of the phone page shows the PC's copy of a phone file, its key its rank; a
tile of `/person` a photo of a face, its key the face's number. The page's own table
turns a key into a file; that file is named only when the index holds it: never a path
sent by the page, never a file set aside (0518) but to take it out.
"""

from __future__ import annotations

import sqlite3
from contextlib import closing
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.index.read_only import connect_read_only
from media_hygiene.search.aside_filter import AsideFilter
from media_hygiene.services.albums import album_desk
from media_hygiene.services.aside_paths import set_aside
from media_hygiene.share.album_pickers import KeyPicker

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Response
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_api import AlbumDesk

    type Keyed = Callable[[str], Path | None]

_KNOWN: Final = "SELECT 1 FROM files WHERE path = ?"


def keyed_albums(
    runtime: Runtime,
    source: Keyed,
    tv: Callable[[tuple[Path, ...]], Response] | None = None,
) -> AlbumDesk:
    """A page's albums, its keys turned into files of the index.

    Args:
        runtime: Settings, mount points and output.
        source: The file a key of the page names, by the page's own table.
        tv: Shows files on the home server's slideshow (0454); None: the page cannot.

    Returns:
        The desk; a key the index does not hold names nothing.
    """
    indexed = partial(_indexed, (runtime.index_file, source))
    aside = AsideFilter(partial(set_aside, runtime), runtime.mapper)
    return album_desk(runtime, KeyPicker(indexed, aside).files, tv)


def _indexed(where: tuple[Path | None, Keyed], key: str) -> Path | None:
    """The file a key names, when the index holds it.

    Args:
        where: The index file (None: none yet) and the page's table.
        key: A key sent by the page.

    Returns:
        The file, in the container; None for an unknown key or a file not indexed.
    """
    index, source = where
    found = source(key)
    if found is None or index is None or not index.is_file():
        return None
    try:
        with closing(connect_read_only(index)) as connection:
            row = connection.execute(_KNOWN, (str(found),)).fetchone()
    except sqlite3.Error:
        return None
    return None if row is None else found
