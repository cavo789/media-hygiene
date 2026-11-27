"""The library's questions answered at once: a search, a choice, a folder, a place.

They run one at a time, in the order sent, in a thread beside the event loop
(`answer_in_turn`): before, each one held the server for its whole length and the
thumbnails waited behind it (measured on the maintainer's PC: 2.8 s for each
thumbnail behind a search of 1.6 s and a place of 1.2 s, 2026-11-15).
"""

from __future__ import annotations

import asyncio
from functools import partial
from typing import TYPE_CHECKING

from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.folders import FOLDER_POSTS
from media_hygiene.search.found_answer import found_answer
from media_hygiene.search.people_desk import PEOPLE_REJECT_PATH
from media_hygiene.search.people_why import PEOPLE_WHY_PATH, why_answer
from media_hygiene.search.place_desk import PLACE_PATH
from media_hygiene.search.tag_desk import HAND_TAG_PATH as HAND

if TYPE_CHECKING:
    from collections.abc import Callable

    from media_hygiene.review.http import Request, Response
    from media_hygiene.search.coverage import CoverageKept
    from media_hygiene.search.place import SearchPlace


async def answer_in_turn(
    place: SearchPlace, coverage: CoverageKept, request: Request
) -> Response:
    """Answer a question of the page off the event loop, after the ones before it.

    Args:
        place: What the library knows.
        coverage: The coverage kept between searches.
        request: The request, checked.

    Returns:
        The response.
    """
    async with place.turn:
        return await asyncio.to_thread(answer_now, place, coverage, request)


async def in_turn[T](place: SearchPlace, work: Callable[[], T]) -> T:
    """Run work that reads the index's connection, in the same turn as the questions.

    The connection is shared: a `GET` answered on the event loop while a question ran
    in its thread failed (`create_function` beside an open statement, 2026-11-16).

    Args:
        place: What the library knows, its turn included.
        work: The work.

    Returns:
        What it returned.
    """
    async with place.turn:
        return await asyncio.to_thread(work)


def answer_now(
    place: SearchPlace, coverage: CoverageKept, request: Request
) -> Response:
    """Answer a question of the page that needs no waiting.

    Args:
        place: What the library knows.
        coverage: The coverage kept between searches.
        request: The request, checked.

    Returns:
        The response.
    """
    answers: dict[str, Callable[[bytes], Response]] = {
        CHOSEN_PATH: place.chosen.answer,
        PEOPLE_REJECT_PATH: place.names.answer,
        PEOPLE_WHY_PATH: partial(why_answer, place.names),
        **place.rules.posts(),
        **({HAND: place.tags.answer} if place.tags else {}),
        **({PLACE_PATH: place.places.answer} if place.places else {}),
        **(place.sort_setup.posts() if place.sort_setup else {}),
    }
    if request.path in answers:
        return answers[request.path](request.body)
    if request.path in FOLDER_POSTS:
        return place.folders.answer(request.path, request.body)
    return found_answer(place, coverage, request.body)
