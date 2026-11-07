"""The routes of `undo --pick` (0525): the quarantine's tiles, and *Restore*.

`GET /` the page, `GET /api/state` the files of every quarantine, `GET /api/file` the
same read again, `GET /preview/<key>.jpg` and `GET /original/<key>.<ext>` a file as it
lies in the quarantine, untouched; `POST /api/restore` (a JSON body: the browser asks
first for another site) puts the files picked back, a partial undo of their runs, and
answers with what is on the disk afterwards.
"""

from __future__ import annotations

import asyncio
from dataclasses import dataclass
from http import HTTPStatus
from typing import TYPE_CHECKING, Final, override

from pydantic import BaseModel, ConfigDict, Field, ValidationError

from media_hygiene.errors import MediaHygieneError
from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.files import file_response
from media_hygiene.review.http import Response
from media_hygiene.review.local_app import LocalApp, choice_failed, page_or_state
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.services.quarantine_pick import (
    QuarantineState,
    quarantine_state,
    restore_picked,
    source_of,
)

if TYPE_CHECKING:
    from concurrent.futures import Executor
    from pathlib import Path

    from media_hygiene.i18n.live import Page
    from media_hygiene.review.http import Request
    from media_hygiene.services.runtime import Runtime

RESTORE_PATH: Final = "/api/restore"


class _Picked(BaseModel):
    """`POST /api/restore`: the keys of the tiles picked."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    keys: tuple[str, ...] = Field(min_length=1)


@dataclass(frozen=True, slots=True)
class _Files:
    """What `file_response` reads: the state again, and each tile's file."""

    runtime: Runtime

    def on_disk(self) -> QuarantineState:
        """Read the quarantine again from the journals and the disk.

        Returns:
            Its tiles.
        """
        return quarantine_state(self.runtime)

    def preview_source(self, key: str) -> Path | None:
        """Find the quarantined file a key names.

        Args:
            key: The tile's key.

        Returns:
            The file, or None.
        """
        return source_of(self.runtime, key)


@dataclass(frozen=True, slots=True)
class QuarantineApp(LocalApp):
    """Answers the browser: the quarantine is read again for every request."""

    runtime: Runtime
    page: Page
    executor: Executor

    @override
    async def answer(self, request: Request) -> Response:
        """Route a request from the loopback.

        Args:
            request: The request.

        Returns:
            The response.
        """
        files = _Files(self.runtime)
        if request.method == "GET":
            pool = PreviewPool(self.executor, self.runtime.previews_dir)
            found = await file_response(request.path, files, pool)
            if found is not None:
                return found
            return page_or_state(request.path, self.page, files.on_disk)
        if request.path != RESTORE_PATH or request.method != "POST":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        return await self._restore(request)

    async def _restore(self, request: Request) -> Response:
        """Answer `POST /api/restore`: the files picked put back, then the state.

        Args:
            request: The request, with a JSON body.

        Returns:
            What came back, read from the disk; 400 or 422 when refused.
        """
        refused = refused_post(request)
        if refused is not None:
            return refused
        try:
            keys = _Picked.model_validate_json(request.body).keys
        except ValidationError:
            return Response(HTTPStatus.BAD_REQUEST)
        try:
            restored = await asyncio.to_thread(restore_picked, self.runtime, keys)
        except (MediaHygieneError, OSError) as exc:
            return choice_failed(exc)
        return json_response(HTTPStatus.OK, restored.model_dump(mode="json"))
