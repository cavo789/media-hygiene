"""The routes of *Try on one month* (0640): the offer, the trial, the rest.

The trial answers its photos as the search's tiles, at their new place; ↶ Undo is the
page's own `/api/undo-run`.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.errors import MediaHygieneError
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.search.days import NAME as DAY
from media_hygiene.search.hits import hit_of, with_facts
from media_hygiene.search.models import Found
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request
    from media_hygiene.search.events_desk import EventsDesk

TRIAL_PATH: Final = "/api/sort/trial"
TRIAL_RUN_PATH: Final = "/api/sort/trial/run"
TRIAL_REST_PATH: Final = "/api/sort/trial/rest"
TRIAL_POSTS: Final = frozenset({TRIAL_RUN_PATH, TRIAL_REST_PATH})
TRIAL_SCRIPT_PATHS: Final = {  # what the page's script calls them
    "trial": TRIAL_PATH,
    "trialRun": TRIAL_RUN_PATH,
    "trialRest": TRIAL_REST_PATH,
}
_ROWS: Final = (
    f"SELECT rowid, path, size, mtime_ns, {DAY}(media_date) FROM files"  # noqa: S608
    " WHERE path IN ({marks})"
)
_MARKS_AT_ONCE: Final = 500  # SQLite limits the parameters of one query


def trial_offer(desk: EventsDesk) -> Response:
    """What *Try on one month* says.

    Args:
        desk: The Events view.

    Returns:
        `{"offer": … or null}`.
    """
    offer = desk.trial.offer() if desk.trial is not None else None
    return json_response(HTTPStatus.OK, {"offer": offer})


async def trial_post(desk: EventsDesk | None, request: Request) -> Response:
    """Run the trial or the rest, in a thread: the page waits for the answer.

    Args:
        desk: The Events view; None: the page has none.
        request: `POST` of one of the two routes.

    Returns:
        The run read back, with the photos of a trial; 409 with the sentence to show.
    """
    refused = refused_post(request)
    if refused is not None:
        return refused
    trial = desk.trial if desk is not None else None
    if desk is None or trial is None:
        return Response(HTTPStatus.NOT_FOUND)
    wanted = trial.run if request.path == TRIAL_RUN_PATH else trial.rest
    try:
        done = await asyncio.to_thread(wanted)
    except MediaHygieneError as exc:
        said = " ".join(filter(None, (exc.message, exc.tip)))
        return json_response(HTTPStatus.CONFLICT, {"error": said})
    return json_response(
        HTTPStatus.OK,
        {
            "run_id": done.run_id,
            "moved": done.moved,
            "verified": done.verified,
            "intact": done.intact,
            "rest": done.rest,
            "hits": _tiles(desk, done.targets),
        },
    )


def _tiles(desk: EventsDesk, targets: tuple[Path, ...]) -> object:
    """The files moved as the search's tiles, in the order of their folders.

    Args:
        desk: The Events view.
        targets: Where they went.

    Returns:
        The tiles the index holds.
    """
    paths = [str(target) for target in targets]
    by_path = {}
    for start in range(0, len(paths), _MARKS_AT_ONCE):
        part = paths[start : start + _MARKS_AT_ONCE]
        query = _ROWS.format(marks=", ".join("?" * len(part)))
        for row in desk.index.connection.execute(query, part):
            by_path[str(row[1])] = row
    hits = tuple(hit_of((None, {}), by_path[path]) for path in paths if path in by_path)
    found = with_facts(desk.index, Found(len(hits), hits))
    return found_view(found, desk.mapper, desk.chosen())["hits"]
