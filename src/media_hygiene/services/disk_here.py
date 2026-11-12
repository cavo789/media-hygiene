"""`/disk-space/`: the disk space page, in the home page's own server (0539).

`GET /disk-space/` the page, `GET …/api/state` the sizes and limits read from the disk,
`POST …/api/limits` writes both limits, `POST …/api/empty` removes the previews: each
answer is the state read again; `POST …/api/purge` hands a run shown on the quarantine's
page to `mh` (0616), the next states reading it back. JSON only, loopback only: a phone
never reaches it.
"""

from __future__ import annotations

import asyncio
import logging
import tomllib
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import ValidationError

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.served_more import DISK_PURGE_PATH
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.review.step_watch import DISK_PAGE
from media_hygiene.services.disk_only import only_answer
from media_hygiene.services.disk_purge import (
    PurgeAsking,
    purge_response,
    read_back,
)
from media_hygiene.services.disk_space import (
    Limits,
    disk_state,
    empty_previews,
    save_limits,
)

if TYPE_CHECKING:
    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime
    from media_hygiene.services.runtime import Runtime

DISK_PREFIX: Final = DISK_PAGE.removesuffix("/")
_STATE: Final = f"{DISK_PAGE}api/state"
_LIMITS: Final = f"{DISK_PAGE}api/limits"
_EMPTY: Final = f"{DISK_PAGE}api/empty"
_ONLY: Final = f"{DISK_PAGE}api/only"  # a run's only copies, before Purge (0699)
_TEMPLATES: Final = "media_hygiene.review"
_LOGGER: Final = logging.getLogger(__name__)


def _state_answer(runtime: Runtime, asking: PurgeAsking | None = None) -> Response:
    """The state, read from the disk.

    Args:
        runtime: Settings and mount points.
        asking: The last purge asked from the page, to read back.

    Returns:
        JSON.
    """
    purged = None if asking is None else read_back(runtime, asking)
    state = disk_state(runtime).model_copy(update={"purged": purged})
    body = state.model_dump_json().encode()
    return Response(HTTPStatus.OK, body, ContentType.JSON)


def _page() -> bytes:
    """Render the page.

    Returns:
        It, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    return headed_page(environment, "disk_space.html.j2", {})


def _write(
    runtime: Runtime, request: Request, asking: PurgeAsking | None = None
) -> Response:
    """Do what a `POST` asks, then read the state again.

    Args:
        runtime: Settings and mount points.
        request: The request.
        asking: The last purge asked from the page, to read back.

    Returns:
        The state; 400 on a bad body, 500 with the sentence when it failed.
    """
    try:
        if request.path == _LIMITS:
            limits = Limits.model_validate_json(request.body)
            save_limits(runtime.locations.config_file, limits)
        else:
            empty_previews(runtime)
    except ValidationError:
        return Response(HTTPStatus.BAD_REQUEST)
    except (OSError, ValueError, tomllib.TOMLDecodeError) as exc:
        _LOGGER.exception("disk space: %s", request.path)
        message = _("That could not be done: {reason}").format(reason=exc)
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": message})
    return _state_answer(runtime, asking)


def _read(
    runtime: Runtime, request: Request, asking: PurgeAsking | None = None
) -> Response:
    """Answer a `GET`: the page, or the state.

    Args:
        runtime: Settings and mount points.
        request: The request.
        asking: The last purge asked from the page, to read back.

    Returns:
        The response; 404 for anything else.
    """
    if request.method == "GET" and request.path == DISK_PAGE:
        return Response(HTTPStatus.OK, _page(), ContentType.HTML)
    if request.method == "GET" and request.path == _STATE:
        return _state_answer(runtime, asking)
    if request.method == "GET" and request.path == _ONLY:
        return only_answer(runtime, request)
    return Response(HTTPStatus.NOT_FOUND)


class DiskHere:
    """The disk space page: settings read again at each request."""

    def __init__(self, fresh: FreshRuntime) -> None:
        """Remember where the settings come from.

        Args:
            fresh: The server's settings, read again when their files change.
        """
        self._fresh = fresh
        self._asking: PurgeAsking | None = None

    @staticmethod
    def serves(path: str) -> bool:
        """Tell whether a path is this page's.

        Args:
            path: The request's path.

        Returns:
            True for the prefix and under it.
        """
        return path == DISK_PREFIX or path.startswith(DISK_PAGE)

    async def handle(self, request: Request) -> Response:
        """Answer a request.

        Args:
            request: The request.

        Returns:
            The response; 403 off the PC's door.
        """
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        path, runtime = request.path, self._fresh.runtime()
        if path == DISK_PREFIX:
            return Response(HTTPStatus.SEE_OTHER, headers=(f"Location: {DISK_PAGE}",))
        if request.method == "POST" and path == DISK_PURGE_PATH:
            answer, asking = await purge_response(runtime, request)
            self._asking = asking or self._asking
            return answer
        if request.method == "POST" and path in {_LIMITS, _EMPTY}:
            refused = refused_post(request)
            if refused is not None:
                return refused
            return await asyncio.to_thread(_write, runtime, request, self._asking)
        return await asyncio.to_thread(_read, runtime, request, self._asking)
