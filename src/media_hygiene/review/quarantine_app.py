"""The routes of `undo --pick` (0525): the quarantine's tiles, and *Restore*.

`GET /` the page, `GET /api/state` the files of every quarantine, `GET /api/file` the
same read again, `GET /preview/<key>.jpg` and `GET /original/<key>.<ext>` a file as it
lies in the quarantine, untouched; `POST /api/restore` (a JSON body: the browser asks
first for another site) puts the files picked back, a partial undo of their runs, and
answers with what is on the disk afterwards.
"""

from __future__ import annotations

from dataclasses import dataclass
from functools import partial
from typing import TYPE_CHECKING, Final, override

from media_hygiene.report.preview_cache import PreviewPool
from media_hygiene.review.local_app import LocalApp
from media_hygiene.review.picked_route import (
    ACT_PATH,
    TileFiles,
    TileRoutes,
    tile_route,
)
from media_hygiene.services.quarantine_pick import (
    quarantine_state,
    restore_picked,
    source_of,
)

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.i18n.live import Page
    from media_hygiene.review.http import Request, Response
    from media_hygiene.services.runtime import Runtime

RESTORE_PATH: Final = ACT_PATH


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
        runtime = self.runtime
        files = TileFiles(
            lambda: quarantine_state(runtime), lambda key: source_of(runtime, key)
        )
        pool = PreviewPool(self.executor, runtime.previews_dir)
        act = partial(restore_picked, runtime)
        return await tile_route(request, TileRoutes(self.page, pool, files, act))
