"""The routes of the *🗂 Events* view: the events made from the index, no classify plan.

`POST` a late photo refused (0558), an event left (0574), an event found in the folders
confirmed (0557), another grouping tried (0643), *Try on one month* (0640); `GET` the
events found, the late photos, the events made from the index (0572) and the trial's
offer. The plan-based choices of review-sort answered here until 0822.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import Response
from media_hygiene.search.events_no_plan import no_plan_post
from media_hygiene.search.found_desk import FOUND_PATH
from media_hygiene.search.grouping_desk import GROUPING_PATH
from media_hygiene.search.late_desk import LATE_PATH, LATE_REFUSE_PATH
from media_hygiene.search.span_events import SPAN_FILES_PATH, SPAN_PATH
from media_hygiene.search.span_left import LEFT_PATH
from media_hygiene.search.trial_api import (
    TRIAL_PATH,
    TRIAL_POSTS,
    TRIAL_SCRIPT_PATHS,
    trial_offer,
    trial_post,
)

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.search.events_desk import EventsDesk


SORT_POSTS: Final = frozenset(
    {FOUND_PATH, LATE_REFUSE_PATH, LEFT_PATH, GROUPING_PATH, *TRIAL_POSTS}
)
SORT_PATHS: Final = dict(TRIAL_SCRIPT_PATHS)  # what the page's script calls them


async def sort_post(desk: EventsDesk | None, request: Request) -> Response:
    """Answer a choice of the Events view.

    Args:
        desk: The Events view; None: the page has none.
        request: `POST` of one of `SORT_POSTS`, checked.

    Returns:
        The answer; 404 when the page has no such part.
    """
    if request.path in TRIAL_POSTS:  # 0640
        return await trial_post(desk, request)
    answer = no_plan_post(desk, request)
    return Response(HTTPStatus.NOT_FOUND) if answer is None else answer


def events_get(desk: EventsDesk | None, path: str) -> Response | None:
    """The events found, the late photos, the events made from the index, the trial.

    Args:
        desk: The Events view; None: the page has none.
        path: `FOUND_PATH`, `TRIAL_PATH`, `LATE_PATH[/<event>]`, `SPAN_PATH…`…

    Returns:
        The view; 404 when the page has no such part; None for another path.
    """
    if desk is None:
        return None
    if path in {TRIAL_PATH, FOUND_PATH} or path.startswith(
        (SPAN_PATH, SPAN_FILES_PATH)
    ):
        return _part(desk, path)
    if not path.startswith(LATE_PATH):
        return None
    late = desk.late
    if late is None:
        return Response(HTTPStatus.NOT_FOUND)
    return late.state() if path == LATE_PATH else late.event(path)


def _part(desk: EventsDesk, path: str) -> Response:
    """The trial's offer, the events found, or the events made from the index.

    Args:
        desk: The Events view.
        path: `TRIAL_PATH`, `FOUND_PATH`, `SPAN_PATH…` or `SPAN_FILES_PATH…`.

    Returns:
        The view; 404 when the page has none.
    """
    if path == TRIAL_PATH:
        return trial_offer(desk)
    if path == FOUND_PATH:
        found = desk.found
        return Response(HTTPStatus.NOT_FOUND) if found is None else found.state()
    span = desk.span
    return Response(HTTPStatus.NOT_FOUND) if span is None else span.answer(path)
