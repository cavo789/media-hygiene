"""`/settings/`: every setting, where it is changed, its value read from disk (0670).

`GET /settings/` renders the page at each request (the values are those `config.toml`
holds now). It changes nothing: each row opens its setting on its own page. PC only:
a phone never reaches it (read-only, and no setting is changed from a phone).
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.i18n.templates import translated_environment
from media_hygiene.review.http import ContentType, Response, is_local
from media_hygiene.review.page_header import headed_page
from media_hygiene.services.settings_index import Listed, config_only, shown_values
from media_hygiene.services.settings_rows import setting_rows

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request
    from media_hygiene.services.fresh_runtime import FreshRuntime

SETTINGS_PAGE: Final = "/settings/"
SETTINGS_TEMPLATE: Final = "settings_index.html.j2"
_PREFIX: Final = SETTINGS_PAGE.removesuffix("/")
_TEMPLATES: Final = "media_hygiene.review"


def settings_page(config_file: Path) -> bytes:
    """Render the page.

    Args:
        config_file: `config.toml`, read now.

    Returns:
        It, in the language in use.
    """
    rows = setting_rows()
    environment = translated_environment(_TEMPLATES, escaped=("html", "j2"))
    listed = [Listed(row, shown_values(config_file, row)) for row in rows]
    return headed_page(
        environment,
        SETTINGS_TEMPLATE,
        {"rows": listed, "only": config_only(rows), "config": str(config_file)},
    )


class SettingsHere:
    """The settings index, in the home page's server."""

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
            True for the page and its prefix.
        """
        return path in {_PREFIX, SETTINGS_PAGE}

    async def handle(self, request: Request) -> Response:
        """Answer a request.

        Args:
            request: The request.

        Returns:
            The page; 403 off the PC's door, 405 for anything but `GET`.
        """
        if not is_local(request):
            return Response(HTTPStatus.FORBIDDEN)
        if request.path == _PREFIX:
            location = f"Location: {SETTINGS_PAGE}"
            return Response(HTTPStatus.SEE_OTHER, headers=(location,))
        if request.method != "GET":
            return Response(HTTPStatus.METHOD_NOT_ALLOWED)
        config = self._fresh.runtime().locations.config_file
        page = await asyncio.to_thread(settings_page, config)
        return Response(HTTPStatus.OK, page, ContentType.HTML)
