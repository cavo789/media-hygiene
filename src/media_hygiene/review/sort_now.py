"""*Sort this event now* (`POST /api/sort-now`): one event's files moved from the page.

The page saved its choice and asked; the server runs `sort` cut to that event in a
thread (the same guards, journal, `undo` and manifest: `services.sort_event`), then
answers with the run as the disk holds it: the files checked at their new place, the
event shown again, sorted. Without a sorter (tests, a page opened read-only) the route
refuses with a sentence.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.sort_state import EventView

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Request, Response

SORT_NOW_PATH: Final = "/api/sort-now"
_FROZEN = ConfigDict(frozen=True, extra="forbid")


class SortNowIn(BaseModel):
    """The event to sort now."""

    model_config = _FROZEN

    event: str


class SortedNow(BaseModel):
    """What the run did, read back: the files at their new place, the event again."""

    model_config = _FROZEN

    run_id: str  # empty: nothing to move, every file already in place
    moved: int
    verified: int  # moves checked at their new place after the run
    intact: bool  # as many files after as before, every move checked
    view: EventView


type Sorter = Callable[[str], SortedNow]


async def sort_now(sorter: Sorter | None, request: Request) -> Response:
    """Sort one event's files, in a thread: the page waits for the answer.

    Args:
        sorter: Runs `sort` cut to an event; None: the page cannot move files.
        request: `POST /api/sort-now`, with the event.

    Returns:
        The run read back, or an error with the sentence to show.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    if sorter is None:
        message = _("This page cannot move files: run 'sort --event' in the terminal.")
        return json_response(HTTPStatus.CONFLICT, {"error": message})
    try:
        asked = SortNowIn.model_validate_json(request.body)
        done = await asyncio.to_thread(sorter, asked.event)
    except ValidationError:
        return json_response(
            HTTPStatus.UNPROCESSABLE_ENTITY, {"error": _("Choose an event.")}
        )
    except MediaHygieneError as exc:
        said = " ".join(filter(None, (exc.message, exc.tip)))
        return json_response(HTTPStatus.CONFLICT, {"error": said})
    return json_response(HTTPStatus.OK, done.model_dump(mode="json"))
