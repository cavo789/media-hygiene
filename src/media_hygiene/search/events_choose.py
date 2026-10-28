"""The choices of the *🗂 Events* view (0438): review-sort's routes, under `/api/sort/`.

Each choice of review-sort (`sort_choices.CHOICES`: an event's folder, photos sent
elsewhere or left, a choice taken back, the sure proposals, the live destination, a
rule) answers here at `/api/sort/<its path>`, on the plan's session the Events view
holds: saved at once in `sort-decisions.json`, read back from the disk, the workbook
value each one saw recorded (`base`). `POST /api/sort/sort-now` moves one event's
files (`sort_now`); `GET /api/sort/rules` and `/api/sort/progress` are *Your rules*
and the progress with the runs. The page then asks the event again for its tiles.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n import _
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.local_app import choice_failed
from media_hygiene.review.serving import json_response
from media_hygiene.review.sort_choices import CHOICES
from media_hygiene.review.sort_now import SORT_NOW_PATH, sort_now
from media_hygiene.review.sort_rule_choices import PROGRESS_PATH, RULES_PATH
from media_hygiene.search.events_desk import EVENTS_PATH

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.review.sort_batch import SortBatchSession
    from media_hygiene.search.events_desk import EventsDesk

SORT_PREFIX: Final = "/api/sort"
_API: Final = "/api"
_VALUE_ERROR: Final = "Value error, "


def sort_path(path: str) -> str:
    """Where a route of review-sort answers on the search page.

    Args:
        path: Its path on review-sort: `/api/event`.

    Returns:
        `/api/sort/event`.
    """
    return SORT_PREFIX + path.removeprefix(_API)


SORT_POSTS: Final = frozenset(sort_path(path) for path in (*CHOICES, SORT_NOW_PATH))
SORT_GETS: Final = frozenset(sort_path(path) for path in (RULES_PATH, PROGRESS_PATH))
SORT_PATHS: Final = {  # what the page's script calls them
    "event": sort_path("/api/event"),
    "files": sort_path("/api/files"),
    "forget": sort_path("/api/forget"),
    "sure": sort_path("/api/sure"),
    "destination": sort_path("/api/destination"),
    "sortNow": sort_path(SORT_NOW_PATH),
    "progress": sort_path(PROGRESS_PATH),
    "rulePreview": sort_path("/api/rule/preview"),
    "rule": sort_path("/api/rule"),
    "rules": sort_path(RULES_PATH),
    "rulesRemove": sort_path("/api/rules/remove"),
}


def choice_answer(session: SortBatchSession, path: str, body: bytes) -> Response:
    """Apply one choice of review-sort and save the decisions file.

    Args:
        session: The plan's session.
        path: The route on review-sort: `/api/event`.
        body: The JSON body.

    Returns:
        What the route answers, as the disk holds it; 422 with a translated reason.
    """
    try:
        view = CHOICES[path](session, body)
    except ValidationError as exc:
        reasons = "; ".join(
            str(error["msg"]).removeprefix(_VALUE_ERROR).rstrip(".")
            for error in exc.errors()
        )
        message = _("Not saved: {reason}.").format(reason=reasons)
        return json_response(HTTPStatus.UNPROCESSABLE_ENTITY, {"error": message})
    except (MediaHygieneError, OSError) as exc:
        return choice_failed(exc)
    return Response(HTTPStatus.OK, view.model_dump_json().encode(), ContentType.JSON)


async def sort_post(desk: EventsDesk | None, request: Request) -> Response:
    """Answer a choice, or *Sort this event now*, of the Events view.

    Args:
        desk: The Events view; None: the page has none.
        request: `POST /api/sort/…`, checked.

    Returns:
        The answer; 404 without a plan.
    """
    try:
        session = desk.session() if desk is not None else None
    except MediaHygieneError:
        session = None
    if desk is None or session is None:
        return Response(HTTPStatus.NOT_FOUND)
    path = _API + request.path.removeprefix(SORT_PREFIX)
    if path == SORT_NOW_PATH:
        return await sort_now(desk.sorter(session), request)
    return choice_answer(session, path, request.body)


def events_get(desk: EventsDesk | None, path: str) -> Response | None:
    """The events, one event, *Your rules*, or the progress and the runs of the plan.

    Args:
        desk: The Events view; None: the page has none.
        path: `/api/events[/<id>]`, `/api/sort/rules` or `/api/sort/progress`.

    Returns:
        The view; 404 without a plan; None for a path of no Events view.
    """
    if desk is None:
        return None
    if path.startswith(EVENTS_PATH):  # 0437
        return desk.state() if path == EVENTS_PATH else desk.event(path)
    if path not in SORT_GETS:
        return None
    try:
        session = desk.session()
    except MediaHygieneError:
        return Response(HTTPStatus.NOT_FOUND)
    if path == sort_path(RULES_PATH):
        body = session.rules_view().model_dump_json()
    else:
        body = session.progress_view().model_dump_json()
    return Response(HTTPStatus.OK, body.encode(), ContentType.JSON)
