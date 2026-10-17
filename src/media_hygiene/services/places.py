"""`media-hygiene places`: the map where the user names their places, until Ctrl+C.

The clusters come from the index (`/cache`). The photos are read only to show the
first ones of a cluster, from the folders mounted read-only, their previews kept in
`/cache`. The places are saved into `/config/config.toml`, which must be mounted and
writable. Like `review`, the
server listens inside the container; Docker publishes it on the host's loopback.
"""

from __future__ import annotations

import asyncio
import contextlib
from functools import partial
from http import HTTPStatus
from importlib.resources import files
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import ConfigError
from media_hygiene.geo.gazetteer import Gazetteer
from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.places.app import (
    FOLDER_PATH,
    PAGE_POLICY,
    PAGE_REFERRER,
    SEARCH_PATH,
    STATE_PATH,
    PlacesApp,
)
from media_hygiene.places.board import PlacesBoard
from media_hygiene.places.clusters import clusters_of
from media_hygiene.places.folder_rows import FolderContext
from media_hygiene.places.folders import FolderDesk
from media_hygiene.places.osm_search import OSM_PATH, online_search
from media_hygiene.places.photos import CLUSTER_PREFIX, FOLDER_PREFIX, FOLDERS_PATH
from media_hygiene.places.posts import ASIDE_PATH, PHOTOS_PATH, SAVE_PATH
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.ending import run_server
from media_hygiene.review.http import ContentType, Response
from media_hygiene.services.missing_mount import missing_mount
from media_hygiene.services.places_index import OpenedMap, located_files, read_index
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.services.next_command import NextVerb
    from media_hygiene.services.runtime import Runtime

_PACKAGE: Final = "media_hygiene.places"
_PAGE_TEMPLATE: Final = "places.html.j2"
_STATIC: Final = "static"
_ASSETS: Final = {
    "/leaflet.js": ("leaflet.js", ContentType.JAVASCRIPT),
    "/leaflet.css": ("leaflet.css", ContentType.CSS),
}


def open_places(runtime: Runtime, again: NextVerb) -> OpenedMap:
    """Check the mounts, read where the photos were taken and the places written.

    Args:
        runtime: Settings, mount points and output.
        again: This command, offered with `/config` added when it is missing.

    Returns:
        The state of the map page: the board, the folders.

    Raises:
        MountError: `/config` is not mounted or not writable.
        ConfigError: The places of `config.toml` are invalid.
    """
    if not runtime.persistent(MountKind.CONFIG):
        raise missing_mount(
            runtime,
            _(
                "The map saves your places in a config.toml file, kept in a folder "
                "of yours mounted on /config: this command has none."
            ),
            again,
        )
    ensure_writable(runtime, MountKind.CONFIG)
    inputs = read_index(runtime)
    located = located_files(inputs)
    if not located:
        runtime.output.warning(
            _("No photo with a GPS position in the index: the map shows no cluster.")
        )
        runtime.output.tip(
            _("Run 'audit' first with the same /cache mount: it records the positions.")
        )
    config_file = runtime.locations.config_file
    towns = Gazetteer.load().renamed(runtime.settings.classify.town_names)
    context = FolderContext(
        config_file, runtime.mapper, runtime.settings.classify, towns
    )
    try:
        board = PlacesBoard(clusters_of(located), context)
        return OpenedMap(board, FolderDesk(inputs, context))
    except ValueError as exc:
        message = _("The places of {file} are invalid: {reason}.")
        host = runtime.mapper.to_host(config_file)
        raise ConfigError(message.format(file=host, reason=exc)) from exc


def serve_places(runtime: Runtime, opened: OpenedMap, port: int) -> None:
    """Serve the map until Ctrl+C; every place is saved as it is named.

    Args:
        runtime: Settings, mount points and output.
        opened: The map's state, and its folders.
        port: The port to listen on, inside the container (0: any free one).
    """
    settings = runtime.settings.places
    osm = online_search(settings.nominatim_url)
    environment = translated_environment(_PACKAGE, escaped=("html", "j2"))
    page = environment.get_template(_PAGE_TEMPLATE).render(
        state_path=STATE_PATH,
        save_path=SAVE_PATH,
        search_path=SEARCH_PATH,
        cluster_path=CLUSTER_PREFIX,
        folders_path=FOLDERS_PATH,
        folder_photos=FOLDER_PREFIX,
        folder_path=FOLDER_PATH,
        aside_path=ASIDE_PATH,
        photos_path=PHOTOS_PATH,
        osm_path=OSM_PATH if osm else "",
        osm_host=osm.host if osm else "",
        tiles=settings.tiles,
        attribution=settings.attribution,
    )
    policy = PAGE_POLICY.format(tiles=settings.tile_host)
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
        policy=policy,
        referrer=PAGE_REFERRER,
    )
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        pool = PreviewPool(executor, runtime.previews_dir)
        app = PlacesApp(opened.board, shown, assets, osm, pool, opened.folders)
        asyncio.run(run_server(app, port, partial(_announce, runtime)))


def _announce(runtime: Runtime, port: int) -> None:
    """Tell where the map is and how to open it from the host.

    Args:
        runtime: Settings, mount points and output.
        port: The port listened on, inside the container.
    """
    output = runtime.output
    output.success(
        _(
            "Map ready, open {url} in your browser. Each place is saved at once in "
            "config.toml. Ctrl+C stops it."
        ).format(url=page_url(port))
    )
    address_tip(output, port)
