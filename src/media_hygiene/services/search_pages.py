"""The pages of `search` and `browse`, one server: the search, the folder view.

Both read the index; the files set aside on either are written into `decisions.json`
of the reports folder, checked writable before each save, for `clean --decisions`.
The server runs until Ctrl+C, or until *Apply now* (`browse` opened from the home
page) ends it on the step that applies the decisions.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.constants import ExitCode
from media_hygiene.errors import MountError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.review.apply_api import APPLY_PATH, ApplyDesk, ApplyOffer
from media_hygiene.review.ending import Ending, EndingDoor, serve_until_ended
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.place import DEFAULT_DECISIONS, decisions_place
from media_hygiene.review.presence import Presence
from media_hygiene.search.app import (
    SEARCH_PAGE_PATH,
    SEARCH_PATH,
    SearchApp,
    SearchPages,
    SearchPlace,
)
from media_hygiene.search.chosen import ChosenPlace, ChosenStore
from media_hygiene.search.chosen_api import CHOSEN_PATH, ChosenDesk
from media_hygiene.search.folders import (
    BROWSE_PATH,
    FOLDER_PATH,
    FOLDERS_PATH,
    FolderDesk,
)
from media_hygiene.services.albums import album_desk
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.writable import ensure_writable
from media_hygiene.share.album_api import ALBUMS_PATH
from media_hygiene.share.album_pickers import SearchPicker

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.apply_api import ApplyStep
    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.search"
_SEARCH_TEMPLATE: Final = "search.html.j2"
_BROWSE_TEMPLATE: Final = "browse.html.j2"


@dataclass(frozen=True, slots=True)
class PageStart:
    """The port, the page `/` serves (`/search` or `/browse`), and how it is said."""

    port: int
    path: str
    ready: str  # translated, with `{url}`
    # Opened from the home page: the step *Apply now* ends on (None: no button).
    apply: Callable[[], ApplyStep | None] | None = None


@dataclass(frozen=True, slots=True)
class Served:
    """How the pages ended: what is set aside, and the exit code asked for."""

    chosen: int  # read from the disk
    code: int = 0  # `STEP_EXIT_BASE + n`: *Apply now* chose step `n`


def serve_pages(runtime: Runtime, search: SearchIndex, start: PageStart) -> Served:
    """Serve the search and the folder view until Ctrl+C or *Apply now*.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.
        start: The port and the page to announce.

    Returns:
        How many files are set aside when the pages stop, read from the disk, and
        the exit code a page asked for.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    paths = {
        "search_path": SEARCH_PATH,
        "chosen_path": CHOSEN_PATH,
        "browse_path": BROWSE_PATH,
        "search_page": SEARCH_PAGE_PATH,
        "folders_path": FOLDERS_PATH,
        "folder_path": FOLDER_PATH,
        "apply_path": APPLY_PATH,
        "albums_path": ALBUMS_PATH,
        "apply_offered": start.apply is not None,
    }
    pages = SearchPages(
        headed_page(environment, _SEARCH_TEMPLATE, paths),
        headed_page(environment, _BROWSE_TEMPLATE, paths),
        start.path,
    )
    chosen = chosen_desk(runtime, search)
    folders = FolderDesk(search, runtime.mapper, shown_roots(runtime), chosen)
    ending = Ending()
    place = SearchPlace(
        search,
        runtime.mapper,
        runtime.previews_dir,
        runtime.settings.people,
        chosen,
        folders,
        ApplyDesk(ApplyOffer(start.apply, lambda: bool(chosen.paths())), ending),
        album_desk(runtime, SearchPicker(search).files),
    )
    code = 0
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        closing = Presence(ending, ExitCode.PAGE_CLOSED)  # its tab closed (0262)
        door = EndingDoor(SearchApp(place, pages, executor), ending, closing)
        ready = partial(_announce, runtime, start)
        code = asyncio.run(serve_until_ended(door, start.port, ready))
    return Served(len(chosen.paths()), code)


def chosen_desk(runtime: Runtime, search: SearchIndex) -> ChosenDesk:
    """The files set aside from the pages: `decisions.json` in the reports folder.

    Args:
        runtime: Settings, mount points and output.
        search: The open index.

    Returns:
        The desk answering the pages about them.
    """
    reports = runtime.locations.reports_dir
    target = reports / DEFAULT_DECISIONS
    roots = runtime.mounts.data_roots(runtime.locations.data_dir)
    place = ChosenPlace(
        target,
        decisions_place(runtime.mapper, reports, target).host,
        runtime.mapper.roots_on_host(roots),
    )
    return ChosenDesk(
        ChosenStore(place, runtime.mapper), search, partial(_reports_ready, runtime)
    )


def shown_roots(runtime: Runtime) -> tuple[Path, ...]:
    """The top folders of the tree: the mounted ones, or the drives of `/data`.

    Args:
        runtime: Settings, mount points and output.

    Returns:
        Them, in the container.
    """
    data_dir = runtime.locations.data_dir
    roots = runtime.mounts.data_roots(data_dir)
    if roots == (data_dir,) and data_dir.is_dir():
        return tuple(sorted(child for child in data_dir.iterdir() if child.is_dir()))
    return roots


def _reports_ready(runtime: Runtime) -> None:
    """Check, before each save, that the reports folder keeps the decisions file.

    Args:
        runtime: Settings, mount points and output.

    Raises:
        MountError: It is not mounted, or not writable.
    """
    if not runtime.persistent(MountKind.REPORTS):
        raise MountError(
            _("The files set aside are saved in /reports: mount it, or they are lost.")
        )
    ensure_writable(runtime, MountKind.REPORTS)


def _announce(runtime: Runtime, start: PageStart, port: int) -> None:
    """Tell where the page is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        start: The page announced, and how.
        port: The port listened on, inside the container.
    """
    runtime.output.success(start.ready.format(url=page_url(port)))
    address_tip(runtime.output, port)
