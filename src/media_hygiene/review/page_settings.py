"""The routes that save a few settings from any page (0606-0609): one dispatch.

Every page server answers them (`shared_routes`), the slideshow's remote too (PC only);
a phone never reaches one (`write_routes`). The file is `config.toml` of the mounts.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.paths.locations import Locations
from media_hygiene.review.ai_state_api import AI_STATE_PATH, ai_state_route
from media_hygiene.review.setting_group import setting_route
from media_hygiene.review.setting_groups import GROUPS

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request, Response

SETTING_PATHS = frozenset({*GROUPS, AI_STATE_PATH})


async def setting_response(
    request: Request, config_file: Path | None = None
) -> Response:
    """Answer one of `SETTING_PATHS`.

    Args:
        request: The request, for one of them.
        config_file: `config.toml`; the mounted one when None.

    Returns:
        The response.
    """
    config = Locations().config_file if config_file is None else config_file
    if request.path == AI_STATE_PATH:
        return await ai_state_route(config, request)
    return await setting_route(GROUPS[request.path], config, request)
