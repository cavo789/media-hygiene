"""The routes of the people page: the page, the groups, the faces, the photos, names.

`GET /api/groups` the groups, `/api/section/<n>` every face of face `n`'s group,
`/face/<n>.jpg` a face, `/photo/<n>.jpg` its photo; `POST /api/people` names, ignores
or takes faces from someone, in `config.toml`; `POST /api/aside` sets aside the photos
of a group, in the decisions file (`aside.py`). Nothing else is written. Like `review`:
loopback hosts only, JSON bodies only, from the page's own origin.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n import _
from media_hygiene.people.aside import ASIDE_PATH
from media_hygiene.people.changes import NamesAsked, Naming
from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.people.roster import Change
from media_hygiene.people.views import PageView
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.report.thumbnails import REVIEW_EDGE
from media_hygiene.review.config_saving import save_refused
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.local_app import jpeg_response
from media_hygiene.review.serving import json_response, refused_post, serve_connection

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.paths.host_paths import HostPathMapper
    from media_hygiene.people.aside import AsideDesk
    from media_hygiene.people.roster import Roster
    from media_hygiene.review.http import Request

PAGE_PATH: Final = "/"
GROUPS_PATH: Final = "/api/groups"
SECTION_PREFIX: Final = "/api/section/"
FACE_PREFIX: Final = "/face/"
PHOTO_PREFIX: Final = "/photo/"
CHANGE_PATH: Final = "/api/people"
JPEG: Final = ".jpg"
_GET, _POST = "GET", "POST"


@dataclass(frozen=True, slots=True)
class PeopleApp:
    """Answers the browser from the roster; the pictures come from the worker pool."""

    roster: Roster
    mapper: HostPathMapper
    page: bytes
    executor: Executor
    previews: Path | None = None  # the cache folder of previews, if any
    aside: AsideDesk | None = None  # None: no reports folder to set photos aside in

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
            message = _("Open the page at 127.0.0.1 or localhost.")
            return Response(HTTPStatus.FORBIDDEN, message.encode())
        path = request.path
        if request.method == _POST and path == CHANGE_PATH:
            return refused_post(request) or self._change(request)
        if request.method == _POST and path == ASIDE_PATH:
            return refused_post(request) or self._aside(request)
        if request.method != _GET:
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        return await self._get(path)

    async def _get(self, path: str) -> Response:
        """Serve the page, the groups, or a picture.

        Args:
            path: The path asked for.

        Returns:
            The response; 404 for anything else.
        """
        if path == PAGE_PATH:
            return Response(HTTPStatus.OK, self.page, ContentType.HTML)
        if path == GROUPS_PATH:
            return json_response(HTTPStatus.OK, self._state())
        if path.startswith(SECTION_PREFIX):
            key = path.removeprefix(SECTION_PREFIX)
            faces = self.roster.whole(key, self.mapper.to_host)
            return json_response(HTTPStatus.OK, {"faces": faces})
        if path.endswith(JPEG):
            return await self._picture(path)
        return Response(HTTPStatus.NOT_FOUND)

    async def _picture(self, path: str) -> Response:
        """Render a face or a whole photo in the worker pool.

        Args:
            path: `/face/<n>.jpg` or `/photo/<n>.jpg`.

        Returns:
            The JPEG, or 404 for an unknown number or an undecodable photo.
        """
        for prefix in (FACE_PREFIX, PHOTO_PREFIX):
            if not path.startswith(prefix):
                continue
            face = self.roster.board.face(path.removeprefix(prefix).removesuffix(JPEG))
            if face is None:
                break
            if prefix == PHOTO_PREFIX:
                return await jpeg_response(
                    self.executor,
                    PreviewPool(self.executor, self.previews).renderer(REVIEW_EDGE),
                    face.path,
                )
            loop = asyncio.get_running_loop()
            job = CropJob(face.path, face.box)
            image = await loop.run_in_executor(self.executor, face_crop, job)
            if image is None:
                break
            return Response(HTTPStatus.OK, image, ContentType.JPEG, cacheable=True)
        return Response(HTTPStatus.NOT_FOUND)

    def _change(self, request: Request) -> Response:
        """Name, ignore or reject faces in `config.toml`, then send the new state.

        Args:
            request: `POST /api/people`.

        Returns:
            The new state with the line read back from the file, or an error.
        """
        try:
            asked = NamesAsked.model_validate_json(request.body)
            if asked.action != "ignore" and not asked.name.strip():
                raise ValueError(_("type a name first"))  # noqa: TRY301
            roster = self.roster
            naming = Naming(
                asked.name, roster.ids(asked.faces), roster.ids(asked.removed)
            )
            saved = roster.change(Change(asked.action, naming))
        except (ValueError, TypeError, OSError) as exc:  # ValidationError included
            return save_refused(exc)
        return json_response(HTTPStatus.OK, {**self._state(), "saved": saved})

    def _aside(self, request: Request) -> Response:
        """Set aside the photos of a group, or take them back, then send the state.

        Args:
            request: `POST /api/aside`.

        Returns:
            The new state with what the decisions file holds, or an error.
        """
        if self.aside is None:
            return Response(HTTPStatus.NOT_FOUND)
        said = self.aside.answer(self.roster.board, request.body)
        if isinstance(said, Response):
            return said
        return json_response(HTTPStatus.OK, {**self._state(), "aside": said})

    def _state(self) -> dict[str, object]:
        """The groups, each with how many of its photos are set aside.

        Returns:
            The state the page reads.
        """
        aside = frozenset() if self.aside is None else self.aside.paths()
        state = self.roster.state(PageView(self.mapper.to_host, aside))
        return {**state, "can_aside": self.aside is not None, "chosen": len(aside)}
