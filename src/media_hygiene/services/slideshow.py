"""`slideshow`: the photos of a folder, a search or the files set aside, on the TV.

The index is read, never written; the photos are never changed. One server until
Ctrl+C (or *Back to the home page*): the remote at `/` on the PC (its browser opens
there) and on the phones paired by `mh --lan`'s code, the screen at `/screen` on the
TV. No presence: the PC's tab may close while the family watches.
"""

from __future__ import annotations

import asyncio
import contextlib
from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.ending import Ending, EndingDoor, serve_until_ended
from media_hygiene.review.lan import lan_access
from media_hygiene.review.lan_app import LAN_PATH
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.search.pictures import Pictures
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.search import open_search
from media_hygiene.services.slideshow_pick import Pick, picked_slides
from media_hygiene.services.slideshow_say import say_slideshow
from media_hygiene.slideshow.app import (
    SCREEN_PATH,
    SCREENS_PATH,
    SHOW_PATH,
    SLIDES_PATH,
    ShowPages,
    SlideshowApp,
)
from media_hygiene.slideshow.desk import Changes, Desk
from media_hygiene.slideshow.door import Door
from media_hygiene.slideshow.pictures import ShowPictures
from media_hygiene.slideshow.screen_api import (
    CODE_SHOWN,
    ENDED_PREFIX,
    PHOTOS_ONLY,
    WAIT_PREFIX,
)
from media_hygiene.slideshow.screen_jpeg import ScreenJob
from media_hygiene.slideshow.screens import Screens
from media_hygiene.slideshow.show import Show
from media_hygiene.slideshow.slides import Timing

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.slideshow"
_REMOTE_TEMPLATE: Final = "slideshow.html.j2"
_SCREEN_TEMPLATE: Final = "screen.html.j2"


@dataclass(frozen=True, slots=True)
class ShowStart:
    """What to show, and the port of the pages (fixed: the TV keeps a bookmark)."""

    pick: Pick
    port: int


def serve_slideshow(runtime: Runtime, start: ShowStart) -> int:
    """Serve the slideshow until Ctrl+C or *Back to the home page*.

    Args:
        runtime: Settings, mount points and output.
        start: What to show, and the port.

    Returns:
        How many photos the show held.

    Raises:
        MediaHygieneError: Nothing to show.
    """
    with open_search(runtime, words=False) as search:
        picked = picked_slides(runtime, search, start.pick)
        if not picked.slides:
            raise MediaHygieneError(
                _("No photo or video to show: nothing the last audit saw matches."),
                _(
                    "Check the folder as the Explorer shows it, under one of your "
                    "photo folders; a search needs 'tags' first."
                ),
            )
        if picked.found > len(picked.slides):
            runtime.output.warning(
                _(
                    "{found} photos and videos found: the first {shown} by date are "
                    "shown."
                ).format(found=picked.found, shown=len(picked.slides))
            )
        settings = runtime.settings.slideshow
        show = Show(picked.slides, Timing(settings.interval_seconds))
        with runtime.executor_factory() as executor:
            app = _app(runtime, show, _Serving(search, executor, start.port))
            ready = partial(_announce, runtime, app.door)
            with contextlib.suppress(KeyboardInterrupt):
                ending = Ending()
                asyncio.run(
                    serve_until_ended(EndingDoor(app, ending), start.port, ready)
                )
    return len(picked.slides)


@dataclass(frozen=True, slots=True)
class _Serving:
    """The open index, the worker pool, the port."""

    search: SearchIndex
    executor: Executor
    port: int


def _app(runtime: Runtime, show: Show, serving: _Serving) -> SlideshowApp:
    """Build the server's routes.

    Args:
        runtime: Settings, mount points and output.
        show: The show.
        serving: The index, the worker pool, the port.

    Returns:
        The app.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    paths = {
        "screen_path": SCREEN_PATH,
        "slides_path": SLIDES_PATH,
        "show_path": SHOW_PATH,
        "screens_path": SCREENS_PATH,
        "lan_path": LAN_PATH,
        "wait_prefix": WAIT_PREFIX,
        "code_shown": CODE_SHOWN,
        "ended_prefix": ENDED_PREFIX,
        "photos_only": PHOTOS_ONLY,
    }
    lan = lan_access(serving.port) if serving.port else None  # `mh --lan`
    phone_url = "" if lan is None else f"{lan.origin}{PAGE_PATH}"  # shown on the TV
    pages = ShowPages(
        headed_page(environment, _REMOTE_TEMPLATE, paths),
        environment.get_template(_SCREEN_TEMPLATE)
        .render(**paths, phone_url=phone_url)
        .encode(),
    )
    screens = Screens()
    previews = runtime.previews_dir
    pictures = ShowPictures(
        frozenset(slide.key for slide in show.slides),
        Pictures(serving.search, previews, serving.executor),
        ScreenJob(runtime.settings.slideshow.screen_px, previews),
        serving.executor,
    )
    return SlideshowApp(
        Desk(show, screens, Changes()), Door(lan, screens), pages, pictures
    )


def _announce(runtime: Runtime, door: Door, port: int) -> None:
    """Say where the remote is, and how the TV and the phones open the show.

    Args:
        runtime: Settings, mount points and output.
        door: The run's access to the home network, if any.
        port: The port listened on, inside the container.
    """
    runtime.output.success(
        _(
            "Slideshow ready: the remote at {url} on this PC. Ctrl+C stops it; your "
            "photos are not changed."
        ).format(url=page_url(port))
    )
    address_tip(runtime.output, port)
    say_slideshow(runtime.output, door.lan)
