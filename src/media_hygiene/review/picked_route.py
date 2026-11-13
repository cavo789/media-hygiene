"""What the pages acting on picked tiles share: the quarantine's, the damaged files'.

The files a tile names, and the `POST` of the keys picked answered with what the disk
holds afterwards.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.files import file_response
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import choice_failed, page_or_state
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.i18n.live import Page
    from media_hygiene.report.preview_cache import PreviewPool
    from media_hygiene.review.http import Request

ACT_PATH: Final = "/api/restore"  # the action of the keys picked


class PickedKeys(BaseModel):
    """A `POST` of the tiles picked: their keys."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    keys: tuple[str, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class TileFiles:
    """What `file_response` reads: the state again, and each tile's file."""

    state: Callable[[], BaseModel]
    source: Callable[[str], Path | None]

    def on_disk(self) -> BaseModel:
        """Read the page's state again.

        Returns:
            Its tiles.
        """
        return self.state()

    def preview_source(self, key: str) -> Path | None:
        """Find the file a key names.

        Args:
            key: The tile's key.

        Returns:
            The file, or None.
        """
        return self.source(key)


async def picked_answer(
    request: Request, act: Callable[[tuple[str, ...]], BaseModel]
) -> Response:
    """Act on the keys posted, in a thread, and answer what it returned.

    Args:
        request: The request, with a JSON body `{"keys": [...]}`.
        act: What to do with the keys.

    Returns:
        Its answer; 400 for a bad body, 403/415 for a refused post, the error said.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        keys = PickedKeys.model_validate_json(request.body).keys
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    try:
        done = await asyncio.to_thread(act, keys)
    except (MediaHygieneError, OSError) as exc:
        return choice_failed(exc)
    return json_response(HTTPStatus.OK, done.model_dump(mode="json"))


@dataclass(frozen=True, slots=True)
class TileRoutes:
    """A page of tiles to act on: its page, its previews, the files, the action."""

    page: Page
    pool: PreviewPool
    files: TileFiles
    act: Callable[[tuple[str, ...]], BaseModel]


async def tile_route(request: Request, routes: TileRoutes) -> Response:
    """Answer the page, its state, a file, or the `POST` of the keys picked.

    Args:
        request: The request, from the loopback.
        routes: The page's parts.

    Returns:
        The response; 405 for any other `POST`.
    """
    if request.method == "GET":
        found = await file_response(request.path, routes.files, routes.pool)
        if found is not None:
            return found
        return page_or_state(request.path, routes.page, routes.files.on_disk)
    if request.path != ACT_PATH or request.method != "POST":
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    return await picked_answer(request, routes.act)
