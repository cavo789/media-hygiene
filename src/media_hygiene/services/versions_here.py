"""`/settings/versions/`: each saved file's versions, *Restore this one* (0784).

`GET` renders the page with every file and its versions, read now. `POST
/settings/versions/api/restore` (`{"path", "name"}`, JSON only, loopback only) puts a
version back through `file_history.restore_version`: the content read back from the disk
is answered, with the version now keeping what the file held (the toast's Undo restores
it). A version trimmed meanwhile, or a path no history lists: 409, nothing changed.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from pydantic import BaseModel, ConfigDict, ValidationError

from media_hygiene.i18n import _
from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.page_header import headed_page
from media_hygiene.review.serving import json_response, refused_post
from media_hygiene.services.settings_versions import restore_named, saved_files

if TYPE_CHECKING:
    from media_hygiene.paths.locations import Locations
    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime

VERSIONS_PAGE: Final = "/settings/versions/"
VERSIONS_TEMPLATE: Final = "settings_versions.html.j2"
RESTORE_PATH: Final = f"{VERSIONS_PAGE}api/restore"
_TEMPLATES: Final = "media_hygiene.review"
_ENCODING: Final = "utf-8"


class _Asked(BaseModel):
    """`POST …/api/restore`: the file and the version, as the page listed them."""

    model_config = ConfigDict(frozen=True, extra="forbid")

    path: str
    name: str


def _state(locations: Locations) -> list[dict[str, object]]:
    return [each.model_dump(mode="json") for each in saved_files(locations)]


def versions_page(locations: Locations) -> bytes:
    """Render the page.

    Args:
        locations: The mount points, read now.

    Returns:
        It, in the language in use.
    """
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    values = {"files": _state(locations), "restore_path": RESTORE_PATH}
    return headed_page(environment, VERSIONS_TEMPLATE, values)


def restore_answer(locations: Locations, body: bytes) -> Response:
    """Restore the version asked, then say what the disk holds.

    Args:
        locations: The mount points.
        body: `{"path", "name"}`.

    Returns:
        The content read back, the Undo's version, the files again; 400 or 409.
    """
    try:
        asked = _Asked.model_validate_json(body)
    except ValidationError:
        return json_response(HTTPStatus.BAD_REQUEST, {"error": "path, name"})
    try:
        back, kept = restore_named(locations, asked.path, asked.name)
    except LookupError:
        said = _(
            "This version is not kept any more (trimmed meanwhile): nothing was "
            "changed."
        )
        return json_response(HTTPStatus.CONFLICT, {"error": said})
    except OSError as exc:
        return json_response(HTTPStatus.INTERNAL_SERVER_ERROR, {"error": str(exc)})
    answer: dict[str, object] = {
        "path": asked.path,
        "content": back.decode(_ENCODING, errors="replace"),
        "kept": kept,
        "files": _state(locations),
    }
    return json_response(HTTPStatus.OK, answer)


class VersionsHere:
    """The versions page, in the home page's server (PC only)."""

    def __init__(self, fresh: FreshRuntime) -> None:
        """Remember where the settings come from.

        Args:
            fresh: The server's settings, read again when their files change.
        """
        self._fresh = fresh

    @staticmethod
    def serves(path: str) -> bool:
        """Tell whether a path is this page's.

        Args:
            path: The request's path.

        Returns:
            True for the page and its restore route.
        """
        return path in {VERSIONS_PAGE, RESTORE_PATH}

    async def handle(self, request: Request) -> Response:
        """Answer a request.

        Args:
            request: The request.

        Returns:
            The page, or a restore's answer; 403 off the PC, 405 otherwise.
        """
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        locations = self._fresh.runtime().locations
        if request.path == RESTORE_PATH and request.method == "POST":
            refused = refused_post(request)
            if refused is not None:
                return refused
            return await asyncio.to_thread(restore_answer, locations, request.body)
        if request.path != VERSIONS_PAGE or request.method != "GET":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        page = await asyncio.to_thread(versions_page, locations)
        return Response(HTTPStatus.OK, page, ContentType.HTML)
