"""`POST /api/search`: the files found, marked set aside and in the album named (0501).

Moved out of `search.app` when the album a search is aimed at came in.
"""

from __future__ import annotations

from http import HTTPStatus
from typing import TYPE_CHECKING

from media_hygiene.review.http import Response
from media_hygiene.review.serving import json_response
from media_hygiene.search.album_filter import aimed_query, album_paths, marked
from media_hygiene.search.asked import read_asked
from media_hygiene.search.hits import with_facts
from media_hygiene.search.reading import read_query, search_note
from media_hygiene.search.views import found_view

if TYPE_CHECKING:
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
    aimed = asked.album
    paths = (
        frozenset[str]()
        if aimed is None
        else album_paths(place.albums.store, aimed.name)
    )
    if aimed is not None:
        query = aimed_query(query, aimed, (paths, place.mapper))
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
