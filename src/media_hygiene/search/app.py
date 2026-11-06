"""The routes of the search page, one server.

`GET /` serves the page opened (`/library`, `/browse`, `/events`); `POST /api/search`
the files found; `/thumb/`, `/preview/`, `/original/` the pictures; `/api/chosen`,
albums, *Apply now*, folders, period rules, Events, hand words (0555). Loopback only.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.review.home_views import APPLY_PATH
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import refused_post, serve_connection
from media_hygiene.review.videos import NEAR_POLICY, VIDEO_PREFIX, video_response
from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.coverage import CoverageKept
from media_hygiene.search.date_desk import DATE_PATH
from media_hygiene.search.events_choose import SORT_POSTS, events_get, sort_post
from media_hygiene.search.events_desk import EVENTS_PAGE_PATH
from media_hygiene.search.folders import BROWSE_PATH, FOLDER_POSTS, FOLDERS_PATH
from media_hygiene.search.former_page import LIBRARY_PAGE, moved_page
from media_hygiene.search.found_answer import awaited_answer, found_answer
from media_hygiene.search.people_desk import PEOPLE_REJECT_PATH
from media_hygiene.search.people_why import (
    FACE_CROP_PREFIX,
    PEOPLE_WHY_PATH,
    crop_answer,
    why_answer,
)
from media_hygiene.search.pictures import Pictures
from media_hygiene.search.place_desk import PLACE_PATH
from media_hygiene.search.rule_desk import PERIOD_RULES_PATH, RULE_POSTS
from media_hygiene.search.rule_go import GO_PATHS, go_answer
from media_hygiene.search.sort_folder_desk import SORT_FOLDER_PATH
from media_hygiene.search.sort_setup_desk import SETUP_PATH
from media_hygiene.search.tag_desk import HAND_TAG_PATH as HAND
from media_hygiene.search.undo_api import UNDO_PATH, latest_answer, undo_answer
from media_hygiene.share.album_api import ALBUMS_PATH

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Callable
    from concurrent.futures import Executor

    from media_hygiene.review.http import Request
    from media_hygiene.search.place import SearchPlace

PAGE_PATH: Final = "/"
SEARCH_PAGE_PATH: Final = LIBRARY_PAGE
SEARCH_PATH: Final = "/api/search"
_GET, _POST = "GET", "POST"
_POSTED: Final = frozenset(
    {SEARCH_PATH, CHOSEN_PATH, *FOLDER_POSTS, APPLY_PATH, HAND, UNDO_PATH}
)
_POSTED_TOO: Final = (
    SORT_POSTS
    | {ALBUMS_PATH, PEOPLE_REJECT_PATH, PEOPLE_WHY_PATH}
    | {
        SETUP_PATH,
        SORT_FOLDER_PATH,
        DATE_PATH,
        PLACE_PATH,
    }
)


@dataclass(frozen=True, slots=True)
class SearchPages:
    """The page (`/browse` opens it on its folders), and the path `/` serves."""

    search: bytes
    first: str = SEARCH_PAGE_PATH


@dataclass(frozen=True, slots=True)
class SearchApp:
    """Answers the browser: searches the index, serves the pictures."""

    place: SearchPlace
    pages: SearchPages
    executor: Executor
    coverage: CoverageKept = field(default_factory=CoverageKept)  # 0344

    async def connection(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Serve one connection: one request, one response.

        Args:
            reader: What the browser sends.
            writer: Where to answer.
        """
        await serve_connection(reader, writer, self.handle)

    async def handle(self, request: Request) -> Response:
        """Route a request.

        Args:
            request: The request.

        Returns:
            The response.
        """
        if not is_local(request):
            message = _("Open the search at 127.0.0.1 or localhost.")
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        if (moved := moved_page(request)) is not None:
            return moved
        if request.method == _GET:
            return await self._get(request)
        if (
            request.method != _POST
            or request.path not in _POSTED | _POSTED_TOO | RULE_POSTS | GO_PATHS
        ):
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        refused = refused_post(request)
        if refused is not None:
            return refused
        return await self._post(request)

    async def _post(self, request: Request) -> Response:
        """Answer a JSON body from the page: a search, a folder, a choice, an album.

        Args:
            request: The request, checked.

        Returns:
            The response.
        """
        if (awaited := awaited_answer(self.place, request)) is not None:
            return await awaited
        if request.path == UNDO_PATH and self.place.undo is not None:  # 0601
            return await undo_answer(self.place.undo, request.body)
        if request.path in GO_PATHS | SORT_POSTS:  # a rule's GO, the Events (0438)
            return await (
                sort_post(self.place.events, request)
                if request.path in SORT_POSTS
                else go_answer(self.place.rules, request.path, request.body)
            )
        answers: dict[str, Callable[[bytes], Response]] = {
            CHOSEN_PATH: self.place.chosen.answer,
            PEOPLE_REJECT_PATH: self.place.names.answer,
            PEOPLE_WHY_PATH: partial(why_answer, self.place.names),
            **self.place.rules.posts(),
            **({HAND: self.place.tags.answer} if self.place.tags else {}),
            **({PLACE_PATH: self.place.places.answer} if self.place.places else {}),
            **(self.place.sort_setup.posts() if self.place.sort_setup else {}),
        }
        if request.path in answers:
            return answers[request.path](request.body)
        if request.path in FOLDER_POSTS:
            return self.place.folders.answer(request.path, request.body)
        return found_answer(self.place, self.coverage, request.body)

    async def _get(self, request: Request) -> Response:
        """Serve a page, what is set aside, the tree, a picture or a video.

        Args:
            request: The request.

        Returns:
            The response; 404 for anything else, an unknown key, or a file that
            cannot be shown.
        """
        path = self.pages.first if request.path == PAGE_PATH else request.path
        # One page (0408): `/browse` is the search, folders open; videos: `media-src`.
        if path in {SEARCH_PAGE_PATH, BROWSE_PATH, EVENTS_PAGE_PATH}:
            return Response(
                HTTPStatus.OK, self.pages.search, ContentType.HTML, policy=NEAR_POLICY
            )
        states: dict[str, Callable[[], Response]] = {
            CHOSEN_PATH: self.place.chosen.state,
            ALBUMS_PATH: self.place.albums.state,
            FOLDERS_PATH: self.place.folders.tree,
            PERIOD_RULES_PATH: self.place.rules.state,
            **(
                {UNDO_PATH: partial(latest_answer, self.place.undo)}
                if self.place.undo
                else {}
            ),
            **(self.place.sort_setup.gets() if self.place.sort_setup else {}),
        }
        if path in states:
            return states[path]()
        events = events_get(self.place.events, path)
        if events is not None:  # the Events view (0437, 0438)
            return events
        if path.startswith(FACE_CROP_PREFIX):
            return await crop_answer(self.place.names, path, self.executor)
        pictures = Pictures(self.place.index, self.place.previews, self.executor)
        if path.startswith(VIDEO_PREFIX):
            return await video_response(request, pictures.source)
        answer = await pictures.answer(path)
        return Response(HTTPStatus.NOT_FOUND) if answer is None else answer
