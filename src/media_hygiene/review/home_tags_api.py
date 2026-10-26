"""`/api/tags` of the home page: `tags` run in the page (0343).

`GET` tells where it stands (reopening the page during a run shows the run);
`POST {"action": "prepare"}` writes the cheap words and counts the photos to describe,
`{"action": "describe", "minutes": 60}` sends them (no `minutes`: until done or Stop),
`{"action": "stop"}` stops after the photo in flight. One half at a time: 409 else.
"""

from __future__ import annotations

import asyncio
from enum import StrEnum
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.home_tags import HomeTags

TAGS_PATH: Final = "/api/tags"
_MAX_MINUTES: Final = 24 * 60


class TagsAction(StrEnum):
    """What `POST /api/tags` asks."""

    PREPARE = "prepare"
    DESCRIBE = "describe"
    STOP = "stop"


class _TagsAsked(BaseModel):
    """`POST /api/tags`."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: TagsAction
    minutes: int | None = Field(default=None, ge=1, le=_MAX_MINUTES)


def tags_state(tags: HomeTags) -> Response:
    """`GET /api/tags`.

    Args:
        tags: The page's `tags`.

    Returns:
        Its state, as JSON.
    """
    body = tags.state().model_dump_json().encode()
    return Response(HTTPStatus.OK, body, ContentType.JSON)


async def tags_response(tags: HomeTags, request: Request) -> Response:
    """`POST /api/tags`: prepare, describe or stop.

    Args:
        tags: The page's `tags`.
        request: The request.

    Returns:
        The state; 400 on a bad body, 409 when a half already runs.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    try:
        asked = _TagsAsked.model_validate_json(request.body)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    match asked.action:
        case TagsAction.STOP:
            await asyncio.to_thread(tags.stop)
            started = True
        case TagsAction.PREPARE:
            started = tags.prepare()
        case _:
            started = tags.describe(asked.minutes)
    if not started:
        message = _("Tags already run: wait for the end, or stop them.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    return tags_state(tags)
