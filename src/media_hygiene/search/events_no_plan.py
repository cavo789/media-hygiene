"""The choices of the *🗂 Events* view that need no classify plan.

A late photo refused (0558), an event left unsorted (0574), an event found in the
folders confirmed (0557), other grouping values tried (0643).
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Response
from media_hygiene.search.found_desk import FOUND_PATH
from media_hygiene.search.grouping_desk import GROUPING_PATH
from media_hygiene.search.late_desk import LATE_REFUSE_PATH
from media_hygiene.search.span_left import LEFT_PATH, left_answer

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Request
    from media_hygiene.search.events_desk import EventsDesk


def no_plan_post(desk: EventsDesk | None, request: Request) -> Response | None:
    """A choice that needs no plan: a late photo, an event left, found, a grouping.

    Args:
        desk: The Events view; None: the page has none.
        request: `POST /api/sort/…`, checked.

    Returns:
        The answer, 404 when the page has no such part; None for another path.
    """
    if request.path == LEFT_PATH:  # 0574
        return left_answer(desk.span if desk is not None else None, request.body)
    late, found, grouping = (
        (desk.late, desk.found, desk.grouping) if desk else (None, None, None)
    )
    parts: dict[str, Callable[[bytes], Response] | None] = {
        LATE_REFUSE_PATH: late.refuse if late else None,  # 0558
        FOUND_PATH: found.confirm if found else None,  # 0557
        GROUPING_PATH: grouping.answer if grouping else None,  # 0643
    }
    if request.path not in parts:
        return None
    answer = parts[request.path]
    return Response(HTTPStatus.NOT_FOUND) if answer is None else answer(request.body)
