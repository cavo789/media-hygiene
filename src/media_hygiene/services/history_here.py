"""`/history/`: what each run did, in the home page's own server (0350).

A click on *See what each run did* used to end the home server so that `mh` printed
the table in the terminal, leaving the tab as it was. Now the server answers it, read
again from `/journal` each time the page is asked for (it is read-only, 🔒); the cells
are those of `mh history` (`history_rows`).
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final
from urllib.parse import parse_qs

from media_hygiene.errors import MountError
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.served_more import BACK_TO_HISTORY, purge_page
from media_hygiene.review.step_watch import HISTORY_PAGE
from media_hygiene.services.history_rows import HistoryTable, history_table, load_runs
from media_hygiene.services.status import read_status

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.runtime import Runtime

HISTORY_PREFIX: Final = HISTORY_PAGE.removesuffix("/")
PAGE_TEMPLATE: Final = "history.html.j2"
_TEMPLATES: Final = "media_hygiene.review"


def history_page(runtime: Runtime, purged: str = "") -> bytes:
    """Render the page: the table, or the message and hint of `mh history`.

    Args:
        runtime: Settings, mount points and output.
        purged: The run a purge started here was asked for (`?purged=`), read back
            from the disk (0631); empty: none.

    Returns:
        The page, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    error, hint = "", ""
    table = HistoryTable((), (), ())
    purges: dict[str, str] = {}
    gone: bool | None = None
    try:
        table = history_table(load_runs(runtime))
        runs = read_status(runtime).quarantine.runs
        purges = {run.run_id: purge_page(run.run_id, BACK_TO_HISTORY) for run in runs}
        gone = (purged not in purges) if purged else None  # read back from the disk
    except MountError as exc:
        error, hint = str(exc), exc.tip or ""
    values = {
        "table": table,
        "purges": purges,
        "purged": purged,
        "gone": gone,
        "error": error,
        "hint": hint,
    }
    return headed_page(environment, PAGE_TEMPLATE, values)


class HistoryHere:
    """The history page, built again each time it is opened."""

    def __init__(self, fresh: FreshRuntime) -> None:
        """Remember where the settings come from.

        Args:
            fresh: The server's settings, read again when their files change.
        """
        self._fresh = fresh

    async def handle(self, request: Request) -> Response:
        """Answer `GET /history/`.

        Args:
            request: The request.

        Returns:
            The page; a redirect from `/history`; 404 for any other path.
        """
        if request.method != "GET":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        if request.path == HISTORY_PREFIX:
            return Response(
                HTTPStatus.SEE_OTHER, headers=(f"Location: {HISTORY_PAGE}",)
            )
        if request.path != HISTORY_PAGE:
            return Response(HTTPStatus.NOT_FOUND)
        purged = parse_qs(request.query).get("purged", [""])[0]
        page = await asyncio.to_thread(history_page, self._fresh.runtime(), purged)
        return Response(HTTPStatus.OK, page, ContentType.HTML)
