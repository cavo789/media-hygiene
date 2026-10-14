"""The routes of the search page: the page, the search, the previews, the originals.

`GET /` serves the page, `POST /api/search` the files matching the words and filters
sent in JSON, `GET /thumb/<key>.jpg` a small preview (kept in the cache folder),
`GET /preview/<key>.jpg` a large one, `GET /original/<key>.<ext>` the file untouched.
Like `review` and `places`: loopback hosts only, JSON bodies only, from the page's
own origin. Nothing is ever changed: no route writes but the previews' cache.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.review.originals import original_response
from media_hygiene.review.serving import json_response, refused_post, serve_connection
from media_hygiene.search.people_words import unknown_people
from media_hygiene.search.thumbs import GRID_EDGE
from media_hygiene.search.views import (
    JPEG,
    ORIGINAL_PREFIX,
    PREVIEW_PREFIX,
    THUMB_PREFIX,
    SearchAsked,
    found_view,
)

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.config.people_settings import PeopleSettings
    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.review.http import Request
    from media_hygiene.search.fts import SearchIndex

PAGE_PATH: Final = "/"
SEARCH_PATH: Final = "/api/search"
# The page shows this many files at most; the total says how many match.
PAGE_HITS: Final = 240
_GET, _POST = "GET", "POST"


@dataclass(frozen=True, slots=True)
class SearchPlace:
    """Where the search reads, and how it writes paths: index, mapper, previews."""

    index: SearchIndex
    mapper: HostPathMapper
    previews: Path | None  # the cache folder of previews, if any
    people: PeopleSettings  # the names, to say when a `person:` word names nobody


@dataclass(frozen=True, slots=True)
class SearchApp:
    """Answers the browser: searches the index, serves the pictures."""

    place: SearchPlace
    page: bytes
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
            return await self._get(request.path)
        if request.method != _POST or request.path != SEARCH_PATH:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        refused = refused_post(request)
        if refused is not None:
            return refused
        return self._search(request)

    async def _get(self, path: str) -> Response:
        """Serve the page, a preview or an original.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else, an unknown key, or a file that
            cannot be shown.
        """
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.page, ContentType.HTML)
        if path.startswith(ORIGINAL_PREFIX):
            return await original_response(path, self._source)
        for prefix in (THUMB_PREFIX, PREVIEW_PREFIX):
            if path.startswith(prefix) and path.endswith(JPEG):
                return await self._picture(prefix, path)
        return Response(HTTPStatus.NOT_FOUND)

    async def _picture(self, prefix: str, path: str) -> Response:
        """Render a small or a large preview in the worker pool.

        Args:
            prefix: `/thumb/` or `/preview/`.
            path: The path asked for.

        Returns:
            The JPEG, or 404.
        """
        key = path.removeprefix(prefix).removesuffix(JPEG)
        photo = self.place.index.source_of(int(key)) if key.isdigit() else None
        if photo is None:
            return Response(HTTPStatus.NOT_FOUND)
        pool = PreviewPool(self.executor, self.place.previews)
        if prefix == PREVIEW_PREFIX:
            render = pool.renderer(REVIEW_EDGE)
            return await jpeg_response(self.executor, render, photo.path)
        loop = asyncio.get_running_loop()
        render = pool.renderer(GRID_EDGE)
        image = await loop.run_in_executor(self.executor, render, photo.path)
        if image is None:
            return Response(HTTPStatus.NOT_FOUND)
        return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)

    def _source(self, key: str) -> Path | None:
        """The file an original's key names.

        Args:
            key: The key, from the page.

        Returns:
            The file, in the container, or None for an unknown key.
        """
        photo = self.place.index.source_of(int(key)) if key.isdigit() else None
        return None if photo is None else photo.path

    def _search(self, request: Request) -> Response:
        """Find the files matching the words and filters sent.

        Args:
            request: `POST /api/search`.

        Returns:
            The total and the first files; 400 for a body that is not a search.
        """
        try:
            asked = SearchAsked.model_validate_json(request.body)
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        query = asked.query()
        found = found_view(self.place.index.find(query, PAGE_HITS), self.place.mapper)
        unknown = unknown_people(query, self.place.people)
        note = {} if unknown is None else {"note": unknown}
        return json_response(HTTPStatus.OK, {**found, **note})
