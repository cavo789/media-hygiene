"""Routes of the home page: samples, tiles, scan scope, import steps, the safety card.

Samples 0485, tiles 0516; the *Are my photos safe?* card apart from the state (0692).

The first two are not in `lan_paths`: a phone sees the PC's arrangement, never edits
it, and has no random photos.
"""

from __future__ import annotations

import asyncio
import json
from dataclasses import dataclass
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.home_tile_order import save_tiles
from media_hygiene.i18n import _
from media_hygiene.review.home_favourites_api import SavedList, saved_list_response
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.import_chain_api import (
    IMPORT_CHAIN_PATH,
    ChainDoor,
    import_chain_route,
)
from media_hygiene.review.import_steps_api import IMPORT_STEPS_PATH, import_steps_route
from media_hygiene.review.lan_switch_api import LAN_SWITCH_PATH, lan_switch_route
from media_hygiene.review.scan_scope_api import SCOPE_PATH, scope_route

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.home_parts import HomeFindings, HomeSample
    from media_hygiene.review.http import Request

SAMPLES_PATH: Final = "/api/samples"
TILES_PATH: Final = "/api/home-tiles"
SAFETY_PATH: Final = "/api/safety"
MORE_PATHS: Final = {
    "samples": SAMPLES_PATH,
    "tiles": TILES_PATH,
    "safety": SAFETY_PATH,
}
_POST: Final = "POST"


@dataclass(frozen=True, slots=True)
class HomeMore:
    """What the two routes need; None: the route is absent."""

    config_file: Path | None = None
    samples: Callable[[], tuple[HomeSample, ...]] | None = None
    chain: ChainDoor | None = None  # 0604
    safety: Callable[[], HomeFindings] | None = None  # the card, slow (0692)


async def more_response(more: HomeMore, request: Request) -> Response | None:
    """Answer one of the two routes.

    Args:
        more: What they need.
        request: The request.

    Returns:
        The response; None for any other path, or a route absent.
    """
    if request.path == IMPORT_CHAIN_PATH and more.chain is not None:
        return await import_chain_route(more.chain, request)
    if more.config_file is not None:
        saved = await _saved_route(more.config_file, request)
        if saved is not None:
            return saved
    if request.path == SAFETY_PATH and more.safety is not None:
        card = await asyncio.to_thread(more.safety)
        return Response(
            HTTPStatus.OK, card.model_dump_json().encode(), ContentType.JSON
        )
    if request.path == SAMPLES_PATH and more.samples is not None:
        drawn = await asyncio.to_thread(more.samples)
        said = {"samples": [sample.model_dump() for sample in drawn]}
        return Response(HTTPStatus.OK, json.dumps(said).encode(), ContentType.JSON)
    return None


async def _saved_route(config_file: Path, request: Request) -> Response | None:
    """Answer a route that writes `config.toml`.

    Args:
        config_file: `config.toml`.
        request: The request.

    Returns:
        The response; None for any other path.
    """
    routes = {
        SCOPE_PATH: scope_route,  # 0535
        LAN_SWITCH_PATH: lan_switch_route,  # 0605
        IMPORT_STEPS_PATH: import_steps_route,  # 0481
    }
    if request.path in routes:
        return await routes[request.path](config_file, request)
    if request.path == TILES_PATH and request.method == _POST:
        return await saved_list_response(_tiles_list(config_file), request)
    return None


def _tiles_list(config_file: Path) -> SavedList:
    """The list `[home] tiles`.

    Args:
        config_file: `config.toml`.

    Returns:
        How to save it.
    """
    return SavedList(
        partial(save_tiles, config_file),
        "tiles",
        lambda: _("config.toml cannot be written: the tiles were not saved."),
        lambda: _(
            "config.toml cannot be read (a mistake in the file?):"
            " the tiles were not saved."
        ),
    )
