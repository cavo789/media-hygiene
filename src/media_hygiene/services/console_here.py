"""`/console/<step>/`: a read-only console step answered in the page (0567).

`status`, `reports`, `inventory` and `config` chosen on the home page used to print in
the terminal only. The home server runs the same command (`cli/page_capture`) each time
the page is asked for and shows its text; typed in a terminal, nothing changes.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.cli.page_capture import captured_step
from media_hygiene.cli.safety import PAGE_CAPTURED
from media_hygiene.errors import MediaHygieneError
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.page_header import headed_page
from media_hygiene.services.history_here import HISTORY_PREFIX, HistoryHere

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.runtime import Runtime

CONSOLE_PREFIX: Final = "/console"
_TEMPLATES: Final = "media_hygiene.review"


def console_page_path(name: str) -> str:
    """The page of a step.

    Args:
        name: One of `PAGE_CAPTURED`.

    Returns:
        Its path, e.g. `/console/status/`.
    """
    return f"{CONSOLE_PREFIX}/{name}/"


def console_page(runtime: Runtime, name: str) -> bytes:
    """Render the page: what the step printed, or its error, never a traceback.

    Args:
        runtime: Settings, mount points and output.
        name: One of `PAGE_CAPTURED`.

    Returns:
        The page, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    error, text = "", ""
    try:
        text = captured_step(runtime, name)
    except MediaHygieneError as exc:
        error = exc.message
    values = {"text": text, "error": error}
    return headed_page(environment, f"console_{name}.html.j2", values)


class ReadOnlyHere:
    """The pages of the read-only steps (history too), built again each time."""

    def __init__(self, fresh: FreshRuntime) -> None:
        """Remember where the settings come from.

        Args:
            fresh: The server's settings, read again when their files change.
        """
        self._fresh = fresh
        self._history = HistoryHere(fresh)

    @staticmethod
    def serves(path: str) -> bool:
        """Tell whether a path is one of these pages.

        Args:
            path: The request's path.

        Returns:
            True for `/history/` and under `/console/`.
        """
        history = path in {HISTORY_PREFIX, f"{HISTORY_PREFIX}/"}
        return history or path.startswith(f"{CONSOLE_PREFIX}/")

    async def handle(self, request: Request) -> Response:
        """Answer `GET /console/<step>/`, or the history's page.

        Args:
            request: The request.

        Returns:
            The page; a redirect without the last slash; 404 for any other path.
        """
        if not request.path.startswith(f"{CONSOLE_PREFIX}/"):
            return await self._history.handle(request)
        if request.method != "GET":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        name = request.path.removeprefix(f"{CONSOLE_PREFIX}/").removesuffix("/")
        if name not in PAGE_CAPTURED:
            return Response(HTTPStatus.NOT_FOUND)
        wanted = console_page_path(name)
        if request.path != wanted:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {wanted}",))
        runtime = self._fresh.runtime()
        page = await asyncio.to_thread(console_page, runtime, name)
        return Response(HTTPStatus.OK, page, ContentType.HTML)
