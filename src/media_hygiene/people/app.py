"""The routes of the people page: the page, the groups, the faces, the photos, names.

`GET /` serves the page, `GET /api/groups` the groups, `GET /face/<n>.jpg` a face cut
from its photo, `GET /photo/<n>.jpg` the whole photo; `POST /api/people` names,
ignores or takes faces from someone, in `config.toml` only. Nothing else is written,
not even a preview. Like `review` and `places`: loopback hosts only, JSON bodies only,
from the page's own origin.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, Literal

from pydantic import BaseModel, ConfigDict, Field

from media_hygiene.i18n import _
from media_hygiene.people.changes import Naming
from media_hygiene.people.crops import CropJob, face_crop
from media_hygiene.people.roster import Change
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
    from media_hygiene.people.roster import Roster
    from media_hygiene.review.http import Request

PAGE_PATH: Final = "/"
GROUPS_PATH: Final = "/api/groups"
FACE_PREFIX: Final = "/face/"
PHOTO_PREFIX: Final = "/photo/"
CHANGE_PATH: Final = "/api/people"
JPEG: Final = ".jpg"
_GET, _POST = "GET", "POST"
_NAME_LENGTH: Final = 100


class _Asked(BaseModel):
    """`POST /api/people`: what to do with which faces, by board number."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    action: Literal["name", "ignore", "reject"]
    name: str = Field(default="", max_length=_NAME_LENGTH)
    faces: tuple[int, ...] = Field(min_length=1)
    removed: tuple[int, ...] = ()


@dataclass(frozen=True, slots=True)
class PeopleApp:
    """Answers the browser from the roster; the pictures come from the worker pool."""

    roster: Roster
    mapper: HostPathMapper
    page: bytes
    executor: Executor
    previews: Path | None = None  # the cache folder of previews, if any

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
            return json_response(HTTPStatus.OK, self.roster.state(self.mapper.to_host))
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
            asked = _Asked.model_validate_json(request.body)
            if asked.action != "ignore" and not asked.name.strip():
                raise ValueError(_("type a name first"))  # noqa: TRY301
            roster = self.roster
            naming = Naming(
                asked.name, roster.ids(asked.faces), roster.ids(asked.removed)
            )
            saved = roster.change(Change(asked.action, naming))
        except (ValueError, TypeError, OSError) as exc:  # ValidationError included
            return save_refused(exc)
        state = self.roster.state(self.mapper.to_host)
        return json_response(HTTPStatus.OK, {**state, "saved": saved})
