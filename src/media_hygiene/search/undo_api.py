"""`/api/undo-run`: the ↶ Undo of a page's toast reverses the run it made (0601).

`GET` names the journal's latest run (the page compares it with the one seen before
*Apply now*); `POST {"run": id}` undoes it in a thread, then answers the files found
back on the disk. Loopback only, JSON-only `POST`, like every route that writes.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.home_views import UNDO_PATH
from media_hygiene.review.http import Response, is_local
from media_hygiene.review.serving import json_response, refused_post

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.page_undo import PageUndo

__all__ = ["UNDO_PATH", "UndoIn", "latest_answer", "undo_answer", "undo_route"]


class UndoIn(BaseModel):
    """The run the page made."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    run: str


def latest_answer(undo: PageUndo) -> Response:
    """Name the journal's latest run.

    Args:
        undo: The page's Undo.

    Returns:
        `{"run_id": id or null}`.
    """
    return json_response(HTTPStatus.OK, {"run_id": undo.latest()})


async def undo_route(undo: PageUndo, request: Request) -> Response:
    """Answer `/api/undo-run` for a page that serves it beside its own routes (0621).

    Args:
        undo: The page's Undo.
        request: The request; its path is the route's.

    Returns:
        The latest run, or the run reversed; 403 away from the PC.
    """
    if not is_local(request):
        return Response(HTTPStatus.FORBIDDEN)
    if request.method != "POST":
        return latest_answer(undo)
    return refused_post(request) or await undo_answer(undo, request.body)


async def undo_answer(undo: PageUndo, body: bytes) -> Response:
    """Reverse the run named, and say what the disk holds afterwards.

    Args:
        undo: The page's Undo.
        body: `{"run": id}`.

    Returns:
        The counts read back; 400 for a bad body, 409 when the run cannot be undone.
    """
    try:
        asked = UndoIn.model_validate_json(body)
    except ValidationError:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": "run"})
    try:
        done = await asyncio.to_thread(undo.undo, asked.run)
    except MediaHygieneError as exc:
        said = " ".join(filter(None, (exc.message, exc.tip)))
        return json_response(HTTPStatus.CONFLICT, {"error": said})
    return json_response(HTTPStatus.OK, done.said())
