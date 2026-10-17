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
    PAGE_POLICY,
    PAGE_REFERRER,
    SAVE_PATH,
    SEARCH_PATH,
    STATE_PATH,
    PlacesApp,
)
from media_hygiene.places.board import PlacesBoard
from media_hygiene.places.clusters import clusters_of
from media_hygiene.places.osm_search import OSM_PATH, online_search
from media_hygiene.places.photos import CLUSTER_PREFIX
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.ending import run_server
from media_hygiene.review.http import ContentType, Response
from media_hygiene.services.missing_mount import missing_mount
from media_hygiene.services.places_index import located_files
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


def open_places(runtime: Runtime, again: NextVerb) -> PlacesBoard:
    """Check the mounts, read where the photos were taken and the places written.

    Args:
        runtime: Settings, mount points and output.
        again: This command, offered with `/config` added when it is missing.

    Returns:
        The board of the map page.

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
    located = located_files(runtime)
    if not located:
        runtime.output.warning(
            _("No photo with a GPS position in the index: the map shows no cluster.")
        )
        runtime.output.tip(
            _("Run 'audit' first with the same /cache mount: it records the positions.")
        )
    config_file = runtime.locations.config_file
    try:
        return PlacesBoard(
            clusters_of(located),
            config_file,
            Gazetteer.load().renamed(runtime.settings.classify.town_names),
        )
    except ValueError as exc:
        message = _("The places of {file} are invalid: {reason}.")
        host = runtime.mapper.to_host(config_file)
        raise ConfigError(message.format(file=host, reason=exc)) from exc


def serve_places(runtime: Runtime, board: PlacesBoard, port: int) -> None:
    """Serve the map until Ctrl+C; every place is saved as it is named.

    Args:
        runtime: Settings, mount points and output.
        board: The map's state.
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
        app = PlacesApp(board, shown, assets, osm, pool)
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
