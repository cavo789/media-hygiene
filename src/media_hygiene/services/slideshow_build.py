"""The slideshow's app, built for its own server or for the home server's (0417).

Its addresses are relative to the remote's page: the same app answers at `/` when
`slideshow` runs alone, and under `/slideshow/` in the home server; the TV's pages at
`/screen` either way (the plain door has no prefix).
"""

from __future__ import annotations

from dataclasses import dataclass
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.lan_paths import LAN_PATH
from media_hygiene.review.local_app import PAGE_PATH
from media_hygiene.review.page_header import headed_page
from media_hygiene.search.pictures import Pictures
from media_hygiene.services.slideshow_map import map_tiles
from media_hygiene.slideshow.app import ShowPages, SlideshowApp
from media_hygiene.slideshow.chapters import BANNER_SECONDS, TITLE_SECONDS
from media_hygiene.slideshow.pictures import ShowPictures
from media_hygiene.slideshow.routes import SCREENS_PATH, SHOW_PATH, SLIDES_PATH
from media_hygiene.slideshow.screen_api import (
    CODE_SHOWN,
    ENDED_PREFIX,
    PHOTOS_ONLY,
    WAIT_PREFIX,
)
from media_hygiene.slideshow.screen_jpeg import ScreenJob
from media_hygiene.slideshow.tv_door import SCREEN_PATH

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.search.fts import SearchIndex
    from media_hygiene.services.runtime import Runtime
    from media_hygiene.slideshow.desk import Desk
    from media_hygiene.slideshow.door import Door

_PACKAGE: Final = "media_hygiene.slideshow"
_REMOTE_TEMPLATE: Final = "slideshow.html.j2"
_SCREEN_TEMPLATE: Final = "screen.html.j2"
_TELLING: Final = {"title_seconds": TITLE_SECONDS, "banner_seconds": BANNER_SECONDS}


@dataclass(frozen=True, slots=True)
class Serving:
    """The open index, the worker pool, who may come, and where the remote is."""

    search: SearchIndex
    executor: Executor
    door: Door
    remote: str = PAGE_PATH  # the remote's address: `/slideshow/` in the home server
    kept: bool = False  # in the home server: the remote keeps it up (its presence)


def _relative(path: str) -> str:
    """An address of the app, relative to the remote's page and to the TV's.

    Args:
        path: The route, e.g. `/api/slides`.

    Returns:
        E.g. `api/slides`.
    """
    return path.lstrip("/")


def show_app(runtime: Runtime, desk: Desk, serving: Serving) -> SlideshowApp:
    """Build the slideshow's routes.

    Args:
        runtime: Settings, mount points and output.
        desk: The show, the TVs paired, the pages waiting.
        serving: The index, the worker pool, the door, the remote's address.

    Returns:
        The app.
    """
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    tiles = map_tiles(runtime.settings.places)
    paths: dict[str, object] = {
        "map_tiles": tiles.url,
        "map_credit": tiles.credit,
        "screen_path": _relative(SCREEN_PATH),
        "slides_path": _relative(SLIDES_PATH),
        "show_path": _relative(SHOW_PATH),
        "screens_path": _relative(SCREENS_PATH),
        "lan_path": _relative(LAN_PATH),
        "wait_prefix": _relative(WAIT_PREFIX),
        "code_shown": CODE_SHOWN,
        "ended_prefix": _relative(ENDED_PREFIX),
        "photos_only": PHOTOS_ONLY,
    }
    lan = serving.door.lan
    phone_url = "" if lan is None else f"{lan.origin}{serving.remote}"  # on the TV
    pages = ShowPages(
        headed_page(
            environment, _REMOTE_TEMPLATE, {**paths, "presence_kept": serving.kept}
        ),
        environment.get_template(_SCREEN_TEMPLATE)
        .render(**paths, phone_url=phone_url, **_TELLING)
        .encode(),
        tiles.policy,
        tiles.referrer,
    )
    previews = runtime.previews_dir
    pictures = ShowPictures(
        frozenset(slide.key for slide in desk.show.slides),
        Pictures(serving.search, previews, serving.executor),
        ScreenJob(runtime.settings.slideshow.screen_px, previews),
        serving.executor,
    )
    return SlideshowApp(desk, serving.door, pages, pictures)
