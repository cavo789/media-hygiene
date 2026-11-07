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
from media_hygiene.i18n.live import PerLocale
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.album_show import ALBUM_SHOW, SLIDESHOW_PAGE
from media_hygiene.review.home_assets import ASSETS_PREFIX
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.page_header import ALBUMS_DOC, page_header
from media_hygiene.search.album_make_desk import ALBUM_MAKE_PATH, AlbumMakeDesk
from media_hygiene.search.album_move_desk import ALBUM_MOVE_PATH
from media_hygiene.search.album_root_desk import ALBUM_ROOT_PATH, album_root_desk
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.aside_filter import AsideFilter, Kept
from media_hygiene.search.folder_role_desk import RoleDesk
from media_hygiene.services.album_reader import AlbumReader
from media_hygiene.services.albums import album_desk
from media_hygiene.services.aside_paths import set_aside
from media_hygiene.services.search_desks import shown_roots
from media_hygiene.share.album_folder_door import AlbumFolderDoor
from media_hygiene.share.album_link_door import ALBUM_LINK_PATH, AlbumLinkDoor
from media_hygiene.share.album_page import (
    ALBUM_CHANGE_PATH,
    ALBUM_EDIT_PAGE,
    ALBUM_LIST_PATH,
    ALBUM_PREFIX,
    ALBUMS_PAGE,
    PHONE_HEADER,
    TV_PAIRED_PATH,
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
    door = AlbumLinkDoor(
        reader, PerLocale(partial(album_page, link=True))
    )  # used under `mh --lan` (0462)
    parts = AlbumParts(
        PerLocale(album_page),
        reader,
        desk,
        shown,
        PerLocale(album_edit_page),
        door,
        _folder_door(runtime),
        server.tv.paired,
    )
    return AlbumPages(home, parts)


def _folder_door(runtime: Runtime) -> AlbumFolderDoor:
    """The albums' folder, said and changed, and an album's folder made (0625).

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Its door, for the PC alone.
    """
    locations = runtime.locations
    roles = RoleDesk(locations.config_file, runtime.mapper, shown_roots(runtime))
    root = album_root_desk(roles, runtime)
    posts = {
        ALBUM_ROOT_PATH: root.answer,
        ALBUM_MAKE_PATH: AlbumMakeDesk(runtime).answer,
    }
    if root.move is not None:
        posts[ALBUM_MOVE_PATH] = root.move.answer
    return AlbumFolderDoor({ALBUM_ROOT_PATH: root.state}, posts, PHONE_HEADER)


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
                "tv_paired": TV_PAIRED_PATH,  # 📺 on a card, with a TV paired (0523)
                "tv_album": f"{SLIDESHOW_PAGE}{ALBUM_SHOW}",
                "link": ALBUM_LINK_PATH,  # 🔗 Share by link (0462)
                "album_root": ALBUM_ROOT_PATH,  # 📁 Albums folder (0625)
                "album_make": ALBUM_MAKE_PATH,
            },
            albums_path=ALBUM_CHANGE_PATH,  # 📺 On the TV posts its files there
            tv_here=True,
            tv_paired_path=TV_PAIRED_PATH,  # the bar's 📺, with a TV paired (0523)
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
