"""The routes of the damaged files' page (0783): tiles, *Restore*, and its Undo.

`GET /` the page, `GET /api/state` every damaged file with its good copy proven now,
`GET /preview/<key>.jpg` (`<key>~copy.jpg`: its good copy) and `GET /original/...`;
`POST /api/restore` (a JSON body) restores the files picked, journaled, each read back;
`/api/undo-run` the toast's ↶ Undo (`mh undo` of the run the page just made).
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
from media_hygiene.search.undo_api import UNDO_PATH, undo_route
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.repair_pick import (
    repair_state,
    restore_damaged,
    source_of,
)

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.i18n.live import Page
    from media_hygiene.review.http import Request, Response
    from media_hygiene.services.runtime import Runtime

RESTORE_PATH: Final = ACT_PATH


@dataclass(frozen=True, slots=True)
class RepairApp(LocalApp):
    """Answers the browser: the damaged files are read again for every request."""

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
        if request.path == UNDO_PATH:
            return await undo_route(PageUndo(self.runtime), request)
        runtime = self.runtime
        files = TileFiles(
            lambda: repair_state(runtime), lambda key: source_of(runtime, key)
        )
        pool = PreviewPool(self.executor, runtime.previews_dir)
        act = partial(restore_damaged, runtime)
        return await tile_route(request, TileRoutes(self.page, pool, files, act))
