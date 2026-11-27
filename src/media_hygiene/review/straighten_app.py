"""The routes of the *Photos to straighten* page (0810): tiles, *Turn*, *Never turn*.

`GET /` the page, `GET /api/state` every turn *Apply now* would write now,
`GET /preview/<key>.jpg` and `GET /original/...`; `POST /api/restore` (the shared
`ACT_PATH`) turns the photos picked, journaled, each read back; `POST /api/refuse`
keeps their refusal; `/api/undo-run` the toast's ↶ Undo.
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
    picked_answer,
    tile_route,
)
from media_hygiene.search.undo_api import UNDO_PATH, undo_route
from media_hygiene.services.page_undo import PageUndo
from media_hygiene.services.turn_pick import (
    refuse_picked,
    turn_picked,
    turn_source,
    turn_state,
)

if TYPE_CHECKING:
    from concurrent.futures import Executor

    from media_hygiene.i18n.live import Page
    from media_hygiene.review.http import Request, Response
    from media_hygiene.services.runtime import Runtime

TURN_PATH: Final = ACT_PATH
REFUSE_PATH: Final = "/api/refuse"


@dataclass(frozen=True, slots=True)
class StraightenApp(LocalApp):
    """Answers the browser: the turns are read again for every request."""

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
        if request.path == UNDO_PATH:
            return await undo_route(PageUndo(runtime), request)
        if request.path == REFUSE_PATH and request.method == "POST":
            return await picked_answer(request, partial(refuse_picked, runtime))
        files = TileFiles(
            lambda: turn_state(runtime), lambda key: turn_source(runtime, key)
        )
        pool = PreviewPool(self.executor, runtime.previews_dir)
        act = partial(turn_picked, runtime)
        return await tile_route(request, TileRoutes(self.page, pool, files, act))
