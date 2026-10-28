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
from typing import TYPE_CHECKING

from media_hygiene.errors import ConfigError
from media_hygiene.geo.towns_once import shared_towns
from media_hygiene.i18n import _
from media_hygiene.paths.mount_kind import MountKind
from media_hygiene.places.board import PlacesBoard
from media_hygiene.places.clusters import clusters_of
from media_hygiene.places.folder_rows import FolderContext
from media_hygiene.places.folders import FolderDesk
from media_hygiene.review.ending import run_server
from media_hygiene.services.missing_mount import missing_mount
from media_hygiene.services.places_build import places_app
from media_hygiene.services.places_index import OpenedMap, located_files, read_index
from media_hygiene.services.reviewing import address_tip, page_url
from media_hygiene.services.search_app import shown_roots
from media_hygiene.services.writable import ensure_writable

if TYPE_CHECKING:
    from media_hygiene.services.next_command import NextVerb
    from media_hygiene.services.runtime import Runtime


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
    towns = shared_towns().renamed(runtime.settings.classify.town_names)
    context = FolderContext(
        config_file,
        runtime.mapper,
        runtime.settings.classify,
        towns,
        shown_roots(runtime),
        runtime.settings.places.town_hint_km,
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
    with runtime.executor_factory() as executor, contextlib.suppress(KeyboardInterrupt):
        app = places_app(runtime, opened, executor)
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
