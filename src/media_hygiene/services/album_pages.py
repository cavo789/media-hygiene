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
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.aside_filter import AsideFilter, Kept
from media_hygiene.services.album_reader import AlbumReader
from media_hygiene.services.albums import album_desk
from media_hygiene.services.aside_paths import set_aside
from media_hygiene.share.album_link_door import ALBUM_LINK_PATH, AlbumLinkDoor
from media_hygiene.share.album_page import (
    ALBUM_CHANGE_PATH,
    ALBUM_EDIT_PAGE,
    ALBUM_LIST_PATH,
    ALBUM_PREFIX,
    ALBUMS_PAGE,
    AlbumPages,
    AlbumParts,
)
from media_hygiene.share.album_shelf import Shown

if TYPE_CHECKING:
    from media_hygiene.review.ending import Handling
    from media_hygiene.services.home_pages import HomeServer
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.share.album_api import AlbumAsked

_PACKAGE: Final = "media_hygiene.share"
_TEMPLATE: Final = "album.html.j2"
_EDIT_TEMPLATE: Final = "album_edit.html.j2"


def album_pages(runtime: Runtime, home: Handling, server: HomeServer) -> AlbumPages:
    """Put the albums' page in front of the home page.

    Args:
        runtime: Settings, mount points and output.
        home: The home page.
        server: Its pool (makes the pictures) and its TV slot (📺, 0500).

    Returns:
        The albums' routes, passing anything else on to the home page.
    """
    reader = AlbumReader(runtime, server.executor)
    shown = Shown()
    aside = AsideFilter(partial(set_aside, runtime), runtime.mapper)
    desk = album_desk(runtime, partial(_picked, (reader, shown, aside)), server.tv)
    door = AlbumLinkDoor(reader, album_page(link=True))  # used under `mh --lan` (0462)
    parts = AlbumParts(album_page(), reader, desk, shown, album_edit_page(), door)
    return AlbumPages(home, parts)


def album_page(template: str = _TEMPLATE, *, link: bool = False) -> bytes:
    """Render the albums' page; its content comes from the list and each album.

    Args:
        template: The list and the phone's view, or one album to edit (0500).
        link: The read-only page of an album's 24 h link (0462).

    Returns:
        The page.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    return (
        environment.get_template(template)
        .render(
            # served by the home server itself: its way back is a plain link (0356)
            header=replace(page_header(template), shared=True),
            paths={
                "home": PAGE_PATH,
                "list": ALBUM_LIST_PATH,
                "album": ALBUM_PREFIX,
                "change": ALBUM_CHANGE_PATH,
                "assets": ASSETS_PREFIX,
                "doc": served_url(ALBUMS_DOC),
                "list_page": ALBUMS_PAGE,
                "edit_page": ALBUM_EDIT_PAGE,
                "search_page": SEARCH_PAGE_PATH,  # *Add photos* (0501)
                "link": ALBUM_LINK_PATH,  # 🔗 Share by link (0462)
            },
            albums_path=ALBUM_CHANGE_PATH,  # 📺 On the TV posts its files there
            tv_here=True,
            album_link=link,
        )
        .encode()
    )


def album_edit_page() -> bytes:
    """Render one album as tiles to pick and take out, on the PC (0500).

    Returns:
        The page.
    """
    return album_page(_EDIT_TEMPLATE)


def _picked(sources: tuple[AlbumReader, Shown, AsideFilter], asked: AlbumAsked) -> Kept:
    """The files a change names: those of the albums the page was shown, by key.

    A page shown before a file was set aside cannot bring it back (0518), but to
    take it out of an album.

    Args:
        sources: The reader, the keys of the albums' files, the files set aside.
        asked: The change; `all` (every file of a search) means nothing here.

    Returns:
        The files, in the container.
    """
    reader, shown, aside = sources
    found = (reader.source(key) for key in shown.picked(asked.keys))
    files = tuple(file for file in found if file is not None)
    return Kept(files) if asked.action == "remove" else aside.keep(files)
