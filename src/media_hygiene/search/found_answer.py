"""`POST /api/search`: the files found, marked set aside and in the album named (0501).

Moved out of `search.app` when the album a search is aimed at came in.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING, Any

from media_hygiene.review.home_views import APPLY_PATH
from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.album_filter import aimed_query, album_paths, marked
from media_hygiene.search.asked import read_asked
from media_hygiene.search.date_desk import DATE_PATH
from media_hygiene.search.hits import with_facts
from media_hygiene.search.landmark_desk import LANDMARK_PATH
from media_hygiene.search.place_neighbours import among
from media_hygiene.search.reading import read_query, search_note
from media_hygiene.search.views import found_view
from media_hygiene.share.album_api import ALBUMS_PATH

if TYPE_CHECKING:
    from collections.abc import Coroutine

    from media_hygiene.review.http import Request
    from media_hygiene.search.coverage import CoverageKept
    from media_hygiene.search.place import SearchPlace


def found_answer(place: SearchPlace, coverage: CoverageKept, body: bytes) -> Response:
    """Find the files matching the words and filters sent.

    Args:
        place: The index, the files set aside, the albums.
        coverage: What the index can be found by, kept between searches.
        body: The request's body.

    Returns:
        The first files found (the set aside only, on **Show** 🗑; an album's, or
        the others, when asked), marked; 400.
    """
    asked = read_asked(body)
    if isinstance(asked, Response):
        return asked
    query = read_query(place.index, asked.query())
    query = place.chosen.narrow(query, asked.aside)
    if asked.near:
        query = among(place.index, query, asked.near)  # 0554
    if asked.missing == "date" and place.dates is not None:
        place.dates.read_again()  # a sidecar written or undone elsewhere counts
    aimed = asked.album
    paths = (
        frozenset[str]()
        if aimed is None
        else album_paths(place.albums.store, aimed.name)
    )
    if aimed is not None:
        query = aimed_query(query, aimed, (paths, place.mapper))
    if place.places is not None:
        query = place.places.narrow(
            query, asked.place, unplaced=asked.missing == "place"
        )
    found = found_view(
        with_facts(place.index, place.index.find(query, asked.shown)),
        place.mapper,
        place.chosen.paths(),
    )
    if aimed is not None:
        found = marked(found, paths)
    unknown = search_note(asked.query(), query, place.people)
    note = {} if unknown is None else {"note": unknown}
    seen = {"coverage": coverage.of(place.index)}
    return json_response(HTTPStatus.OK, {**found, **note, **seen})


def awaited_answer(
    place: SearchPlace, request: Request
) -> Coroutine[Any, Any, Response] | None:
    """The answers that wait: *Apply now*, an album, days written (0531).

    Args:
        place: The desks.
        request: The request, checked.

    Returns:
        Its answer to wait for; None for another route.
    """
    if request.path == APPLY_PATH:
        return place.apply.answer()
    if request.path == ALBUMS_PATH:
        return place.albums.answer(request.body)
    if request.path == DATE_PATH and place.dates is not None:
        return place.dates.answer(request.body)
    if request.path == LANDMARK_PATH and place.landmark is not None:
        return place.landmark.answer(request.body)
    return None
