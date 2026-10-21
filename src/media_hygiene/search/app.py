"""The routes of the search page and the folder view, one server.

`GET /` serves the page the command opens (`/search` or `/browse`). `POST /api/search`
answers the files matching the words and filters sent in JSON, `GET /thumb/<key>.jpg`
a small preview (kept in the cache folder), `GET /preview/<key>.jpg` a large one,
`GET /original/<key>.<ext>` the file untouched. `GET /api/chosen` says what is set
aside, `POST /api/chosen` sets files aside or takes them out (the decisions file in
the reports folder, `chosen_api`); `POST /api/apply` ends the page on the home page's
step that applies them, when opened from it (`apply_api`). The folder view asks for
its tree, its folders and its videos (`folders`). Like `review` and `places`:
loopback hosts only, JSON bodies only, from the page's own origin. The photos are
never changed: `clean --decisions` moves what was set aside.
"""

from __future__ import annotations

from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.review.apply_api import APPLY_PATH
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.serving import json_response, refused_post, serve_connection
from media_hygiene.review.videos import NEAR_POLICY, VIDEO_PREFIX, video_response
from media_hygiene.search.chosen_api import CHOSEN_PATH
from media_hygiene.search.folders import BROWSE_PATH, FOLDER_PATH, FOLDERS_PATH
from media_hygiene.search.people_words import unknown_people
from media_hygiene.search.pictures import Pictures
from media_hygiene.search.views import SearchAsked, found_view

if TYPE_CHECKING:
    import asyncio
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.apply_api import ApplyDesk
    from media_hygiene.review.http import Request
    from media_hygiene.search.chosen_api import ChosenDesk
    from media_hygiene.search.folders import FolderDesk
    from media_hygiene.search.fts import SearchIndex

PAGE_PATH: Final = "/"
SEARCH_PAGE_PATH: Final = "/search"
SEARCH_PATH: Final = "/api/search"
# The page shows this many files at most; the total says how many match.
PAGE_HITS: Final = 240
_GET, _POST = "GET", "POST"
_POSTED: Final = frozenset({SEARCH_PATH, CHOSEN_PATH, FOLDER_PATH, APPLY_PATH})


@dataclass(frozen=True, slots=True)
class SearchPlace:
    """Where the search reads, and how it writes paths: index, mapper, previews."""

    index: SearchIndex
    mapper: HostPathMapper
    previews: Path | None  # the cache folder of previews, if any
    people: PeopleSettings  # the names, to say when a `person:` word names nobody
    chosen: ChosenDesk  # the files set aside
    folders: FolderDesk  # the folder view
    apply: ApplyDesk  # *Apply now*, opened from the home page


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
        if request.method != _POST or request.path not in _POSTED:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        refused = refused_post(request)
        if refused is not None:
            return refused
        if request.path == APPLY_PATH:
            return await self.place.apply.answer()
        return self._post(request)

    def _post(self, request: Request) -> Response:
        """Answer a JSON body from the page: a search, a folder, a choice.

        Args:
            request: The request, checked.

        Returns:
            The response.
        """
        if request.path == CHOSEN_PATH:
            return self.place.chosen.answer(request.body)
        if request.path == FOLDER_PATH:
            return self.place.folders.listing(request.body)
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
        if path == SEARCH_PAGE_PATH:
            return Response(HTTPStatus.OK, self.pages.search, ContentType.HTML)
        if path == BROWSE_PATH:  # it shows the videos: `media-src` too
            return Response(
                HTTPStatus.OK, self.pages.browse, ContentType.HTML, policy=NEAR_POLICY
            )
        if path == CHOSEN_PATH:
            return self.place.chosen.state()
        if path == FOLDERS_PATH:
            return self.place.folders.tree()
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
        query = asked.query()
        found = found_view(
            self.place.index.find(query, PAGE_HITS),
            self.place.mapper,
            self.place.chosen.paths(),
        )
        unknown = unknown_people(query, self.place.people)
        note = {} if unknown is None else {"note": unknown}
        return json_response(HTTPStatus.OK, {**found, **note})
