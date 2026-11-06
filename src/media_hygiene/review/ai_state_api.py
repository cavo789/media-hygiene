"""The local vision model's state, shown and changed where it acts (0608, 🤖).

`GET /api/ai-state` reads `[classify.ai] url` and `model` from `config.toml`, then asks
the server at `url` (and nowhere else) which models it has installed: found or absent,
no photo sent. `POST` saves `model` (empty: the switch is off, no photo ever leaves)
and reads it back from the disk.
"""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.config.classify_ai import DEFAULT_URL
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.setting_group import (
    Field,
    SettingGroup,
    held,
    setting_route,
)

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request

AI_STATE_PATH: Final = "/api/ai-state"
_TAGS: Final = "/api/tags"
_TIMEOUT: Final = 2.0
_TABLES: Final = ("classify", "ai")
AI_MODEL: Final = SettingGroup(AI_STATE_PATH, _TABLES, (Field("model", ""),))
_AI_URL: Final = SettingGroup(AI_STATE_PATH, _TABLES, (Field("url", DEFAULT_URL),))


def installed_models(url: str) -> list[str] | None:
    """The models the server at `url` has, by its own listing.

    Args:
        url: `[classify.ai] url`.

    Returns:
        Their names; None when the server does not answer.
    """
    if not url.startswith(("http://", "https://")):
        return None
    try:
        with urllib.request.urlopen(  # noqa: S310 - the user's own setting
            url.rstrip("/") + _TAGS, timeout=_TIMEOUT
        ) as answer:
            listing = json.loads(answer.read())
        return sorted(str(one["name"]) for one in listing["models"])
    except OSError, urllib.error.URLError, ValueError, KeyError, TypeError:
        return None


def state_of(config_file: Path) -> dict[str, object]:
    """The page's view: the file's url and model, and what the server lists.

    Args:
        config_file: `config.toml`.

    Returns:
        `url`, `model`, `found` and the installed `models`.
    """
    url = str(held(config_file, _AI_URL)["url"])
    models = installed_models(url)
    return {
        "url": url,
        "model": held(config_file, AI_MODEL)["model"],
        "found": models is not None,
        "models": models or [],
    }


async def ai_state_route(config_file: Path, request: Request) -> Response:
    """`GET` the state, `POST` the model chosen.

    Args:
        config_file: `config.toml`.
        request: The request.

    Returns:
        The state read back; the errors of `setting_route` for a `POST`.
    """
    if request.method == "GET":
        body = await asyncio.to_thread(state_of, config_file)
        return Response(HTTPStatus.OK, json.dumps(body).encode(), ContentType.JSON)
    return await setting_route(AI_MODEL, config_file, request)
