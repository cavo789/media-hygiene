"""The map's app, for its own server or under `/places/` in the home server (0417).

Its addresses are relative to the page: the same app answers at `/` when `places`
runs alone, and under the home server's prefix.
"""

from __future__ import annotations

from http import HTTPStatus
from importlib.resources import files
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.places.app import (
    FOLDER_PATH,
    HINT_PATH,
    PAGE_POLICY,
    PAGE_REFERRER,
    SEARCH_PATH,
    STATE_PATH,
    PlacesApp,
)
from media_hygiene.places.osm_search import OSM_PATH, online_search
from media_hygiene.places.photos import (
    CLUSTER_PREFIX,
    FOLDER_PREFIX,
    FOLDERS_PATH,
    GROUP_PREFIX,
    TREE_PREFIX,
)
from media_hygiene.places.posts import ASIDE_PATH, PHOTOS_PATH, SAVE_PATH
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.page_header import page_header

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.services.places_index import OpenedMap
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.places"
_PAGE_TEMPLATE: Final = "places.html.j2"
_STATIC: Final = "static"
_ASSETS: Final = {
    "/leaflet.js": ("leaflet.js", ContentType.JAVASCRIPT),
    "/leaflet.css": ("leaflet.css", ContentType.CSS),
}


def _here(path: str) -> str:
    """A route, relative to the page.

    Args:
        path: E.g. `/api/state`.

    Returns:
        E.g. `api/state`; empty stays empty.
    """
    return path.removeprefix("/")


def places_app(runtime: Runtime, opened: OpenedMap, executor: Executor) -> PlacesApp:
    """Build the map's routes.

    Args:
        runtime: Settings, mount points and output.
        opened: The map's state, and its folders.
        executor: The worker pool, for the previews.

    Returns:
        The app.
    """
    settings = runtime.settings.places
    osm = online_search(settings.nominatim_url)
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    routes = {
        "state_path": STATE_PATH,
        "save_path": SAVE_PATH,
        "search_path": SEARCH_PATH,
        "cluster_path": CLUSTER_PREFIX,
        "folders_path": FOLDERS_PATH,
        "folder_photos": FOLDER_PREFIX,
        "group_photos": GROUP_PREFIX,
        "tree_photos": TREE_PREFIX,
        "folder_path": FOLDER_PATH,
        "aside_path": ASIDE_PATH,
        "hint_path": HINT_PATH,
        "photos_path": PHOTOS_PATH,
        "osm_path": OSM_PATH if osm else "",
    }
    page = environment.get_template(_PAGE_TEMPLATE).render(
        header=page_header(_PAGE_TEMPLATE),
        **{name: _here(path) for name, path in routes.items()},
        osm_host=osm.host if osm else "",
        tiles=settings.tiles,
        attribution=settings.attribution,
    )
    static = files(_PACKAGE).joinpath(_STATIC)
    assets = {
        path: Response(
            HTTPStatus.OK, static.joinpath(name).read_bytes(), kind, cacheable=True
        )
        for path, (name, kind) in _ASSETS.items()
    }
    shown = Response(
        HTTPStatus.OK,
        page.encode(),
        ContentType.HTML,
        policy=PAGE_POLICY.format(tiles=settings.tile_host),
        referrer=PAGE_REFERRER,
    )
    pool = PreviewPool(executor, runtime.previews_dir)
    return PlacesApp(opened.board, shown, assets, osm, pool, opened.folders)
