"""The albums' page, in front of the home page (0297): on the PC and a paired phone.

`mh` alone serves it at `/albums`; under `mh --lan`, a phone paired by its code opens
it too (`review.lan_app`). A change of an album names files of the albums only: a
phone never adds a file it was not shown.
"""

from __future__ import annotations

from dataclasses import replace
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.docs.served import served_url
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.page_header import ALBUMS_DOC, page_header
from media_hygiene.services.album_reader import AlbumReader
from media_hygiene.services.albums import album_desk
from media_hygiene.share.album_api import ALBUMS_PATH
from media_hygiene.share.album_page import (
    ALBUM_LIST_PATH,
    ALBUM_PREFIX,
    AlbumPages,
    AlbumParts,
)
from media_hygiene.share.album_shelf import Shown

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.review.ending import Handling
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_api import AlbumAsked

_PACKAGE: Final = "media_hygiene.share"
_TEMPLATE: Final = "album.html.j2"


def album_pages(runtime: Runtime, home: Handling, executor: Executor) -> AlbumPages:
    """Put the albums' page in front of the home page.

    Args:
        runtime: Settings, mount points and output.
        home: The home page.
        executor: Makes the pictures.

    Returns:
        The albums' routes, passing anything else on to the home page.
    """
    reader = AlbumReader(runtime, executor)
    shown = Shown()
    desk = album_desk(runtime, partial(_picked, (reader, shown)))
    return AlbumPages(home, AlbumParts(album_page(), reader, desk, shown))


def album_page() -> bytes:
    """Render the albums' page; its content comes from the list and each album.

    Returns:
        The page.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    return (
        environment.get_template(_TEMPLATE)
        .render(
            # served by the home server itself: its way back is a plain link (0356)
            header=replace(page_header(_TEMPLATE), shared=True),
            paths={
                "home": PAGE_PATH,
                "list": ALBUM_LIST_PATH,
                "album": ALBUM_PREFIX,
                "change": ALBUMS_PATH,
                "assets": ASSETS_PREFIX,
                "doc": served_url(ALBUMS_DOC),
            },
        )
        .encode()
    )


def _picked(sources: tuple[AlbumReader, Shown], asked: AlbumAsked) -> tuple[Path, ...]:
    """The files a change names: those of the albums the page was shown, by key.

    Args:
        sources: The reader, and the keys of the albums' files.
        asked: The change; `all` (every file of a search) means nothing here.

    Returns:
        The files, in the container.
    """
    reader, shown = sources
    files = (reader.source(key) for key in shown.picked(asked.keys))
    return tuple(file for file in files if file is not None)
