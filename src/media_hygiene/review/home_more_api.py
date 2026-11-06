"""Routes of the home page: samples (0485), tiles (0516), scan scope, import steps.

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
from media_hygiene.review.scan_scope_api import SCOPE_PATH, scope_route

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.home_parts import HomeSample
    from media_hygiene.review.http import Request

SAMPLES_PATH: Final = "/api/samples"
TILES_PATH: Final = "/api/home-tiles"
MORE_PATHS: Final = {"samples": SAMPLES_PATH, "tiles": TILES_PATH}
_POST: Final = "POST"


@dataclass(frozen=True, slots=True)
class HomeMore:
    """What the two routes need; None: the route is absent."""

    config_file: Path | None = None
    samples: Callable[[], tuple[HomeSample, ...]] | None = None
    chain: ChainDoor | None = None  # 0604


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
    config_file = more.config_file
    if config_file is not None:
        if request.path == SCOPE_PATH:  # 0535
            return await scope_route(config_file, request)
        if request.path == IMPORT_STEPS_PATH:  # 0481
            return await import_steps_route(config_file, request)
        if request.path == TILES_PATH and request.method == _POST:
            return await saved_list_response(_tiles_list(config_file), request)
    if request.path == SAMPLES_PATH and more.samples is not None:
        drawn = await asyncio.to_thread(more.samples)
        said = {"samples": [sample.model_dump() for sample in drawn]}
        return Response(HTTPStatus.OK, json.dumps(said).encode(), ContentType.JSON)
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
