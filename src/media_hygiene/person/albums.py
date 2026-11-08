"""`/person`'s albums API (0657): *Add to an album* and ▶ *Slideshow* of its photos.

Its keys are the numbers of the faces it showed (`FaceShelf`): each names that face's
photo, kept only when the index holds it (`keyed_albums`). Under the home server, the
slideshow's slot reaches it (`door.person_on_tv`), and its page offers ▶ *Slideshow* ▾.
"""

from __future__ import annotations

from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.person.routes import ALBUMS_PATH
from media_hygiene.services.keyed_albums import keyed_albums
from media_hygiene.share.album_route import WithAlbums

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.person.app import PersonApp
    from media_hygiene.person.shelf import FaceShelf
    from media_hygiene.services.runtime import Runtime


def with_albums(app: PersonApp, runtime: Runtime) -> WithAlbums:
    """The person page, answering its albums first.

    Args:
        app: The person page.
        runtime: Settings, mount points and output.

    Returns:
        It, with its albums.
    """
    source = partial(_photo, app.finder.shelf)
    return WithAlbums(app, keyed_albums(runtime, source), ALBUMS_PATH)


def _photo(shelf: FaceShelf, key: str) -> Path | None:
    """The photo of a face the page showed.

    Args:
        shelf: The faces, by number.
        key: A face's number, sent by the page.

    Returns:
        Its photo, in the container; None for an unknown number.
    """
    face = shelf.face(key)
    return None if face is None else face.path
