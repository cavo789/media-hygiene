"""The routes of the search page and the folder view, one server.

`GET /` serves the page the command opens (`/search` or `/browse`). `POST /api/search`
answers the files matching the words and filters sent in JSON, `/thumb/<key>.jpg` a
small preview (in the cache), `/preview/<key>.jpg` a large one, `/original/<key>.<ext>`
the file untouched. `/api/chosen`: what is set aside (the decisions file of the
reports, `chosen_api`); `/api/albums` the albums (`share.album_api`); `/api/apply` ends
the page on the home page's step that applies them (`apply_api`). The folder view asks
for its tree, folders, heaviest files and videos (`folders`); `/api/period-…` try,
write and sort the rule of a period (`rule_desk`, `rule_go`, 0396, 0397). Like `review`
and `places`: loopback hosts only, JSON bodies only, from the page's own origin.
"""

from __future__ import annotations

from dataclasses import dataclass, field
from functools import partial
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.apply_api import APPLY_PATH
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, refused_post, serve_connection
from media_hygiene.review.videos import NEAR_POLICY, VIDEO_PREFIX, video_response
from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.coverage import CoverageKept
from media_hygiene.search.folders import BROWSE_PATH, FOLDER_POSTS, FOLDERS_PATH
from media_hygiene.search.hits import with_facts
from media_hygiene.search.people_desk import PEOPLE_REJECT_PATH
from media_hygiene.search.people_why import (
    FACE_CROP_PREFIX,
    PEOPLE_WHY_PATH,
    crop_answer,
    why_answer,
)
from media_hygiene.search.pictures import Pictures
from media_hygiene.search.reading import read_query, search_note
from media_hygiene.search.rule_desk import PERIOD_RULES_PATH, RULE_POSTS
from media_hygiene.search.rule_go import GO_PATHS, go_answer
from media_hygiene.search.views import SearchAsked, found_view
from media_hygiene.share.album_api import ALBUMS_PATH

if TYPE_CHECKING:
    import asyncio
    from collections.abc import Callable
    from concurrent.futures import Executor

    from media_hygiene.review.http import Request
    from media_hygiene.search.place import SearchPlace

PAGE_PATH: Final = "/"
SEARCH_PAGE_PATH: Final = "/search"
SEARCH_PATH: Final = "/api/search"
# The page shows this many files at most; the total says how many match.
_GET, _POST = "GET", "POST"
_POSTED: Final = frozenset({SEARCH_PATH, CHOSEN_PATH, *FOLDER_POSTS, APPLY_PATH})
_POSTED_TOO: Final = frozenset({ALBUMS_PATH, PEOPLE_REJECT_PATH, PEOPLE_WHY_PATH})


@dataclass(frozen=True, slots=True)
class SearchPages:
    """The two pages: the search, the folder view, and which one `/` serves."""

    search: bytes
    browse: bytes
    first: str = SEARCH_PAGE_PATH  # `/browse` for `browse`


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
        if request.path == APPLY_PATH:
            return await self.place.apply.answer()
        if request.path == ALBUMS_PATH:
            return await self.place.albums.answer(request.body)
        if request.path in GO_PATHS:
            return await go_answer(self.place.rules, request.path, request.body)
        answers: dict[str, Callable[[bytes], Response]] = {
            CHOSEN_PATH: self.place.chosen.answer,
            PEOPLE_REJECT_PATH: self.place.names.answer,
            PEOPLE_WHY_PATH: partial(why_answer, self.place.names),
            **self.place.rules.posts(),
        }
        if request.path in answers:
            return answers[request.path](request.body)
        if request.path in FOLDER_POSTS:
            return self.place.folders.answer(request.path, request.body)
        return self._search(request)

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
        if path in {SEARCH_PAGE_PATH, BROWSE_PATH}:
            return Response(
                HTTPStatus.OK, self.pages.search, ContentType.HTML, policy=NEAR_POLICY
            )
        states = {
            CHOSEN_PATH: self.place.chosen.state,
            ALBUMS_PATH: self.place.albums.state,
            FOLDERS_PATH: self.place.folders.tree,
            PERIOD_RULES_PATH: self.place.rules.state,
        }
        if path in states:
            return states[path]()
        if path.startswith(FACE_CROP_PREFIX):
            return await crop_answer(self.place.names, path, self.executor)
        pictures = Pictures(self.place.index, self.place.previews, self.executor)
        if path.startswith(VIDEO_PREFIX):
            return await video_response(request, pictures.source)
        answer = await pictures.answer(path)
        return Response(HTTPStatus.NOT_FOUND) if answer is None else answer

    def _search(self, request: Request) -> Response:
        """Find the files matching the words and filters sent.

        Args:
            request: `POST /api/search`.

        Returns:
            The total and the first files, those set aside marked; 400 for a body
            that is not a search.
        """
        try:
            asked = SearchAsked.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        query = read_query(self.place.index, asked.query())
        found = found_view(
            with_facts(self.place.index, self.place.index.find(query, asked.shown)),
            self.place.mapper,
            self.place.chosen.paths(),
        )
        unknown = search_note(asked.query(), query, self.place.people)
        note = {} if unknown is None else {"note": unknown}
        coverage = {"coverage": self.coverage.of(self.place.index)}
        return json_response(HTTPStatus.OK, {**found, **note, **coverage})
