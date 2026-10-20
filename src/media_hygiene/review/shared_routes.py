"""What every page's server answers before the page: the theme's files and the docs.

`/assets/` (`home_assets`) holds the fonts and images every page shares; `/docs/`
(`docs_app`) the documentation of the version that runs (0270). Both to the loopback
only, like the pages.
"""

from __future__ import annotations

from typing import TYPE_CHECKING

from media_hygiene.docs.pages import DOCS_PREFIX
from media_hygiene.review.docs_app import docs_response
from media_hygiene.review.home_assets import ASSETS_PREFIX, asset_response
from media_hygiene.review.http import is_local

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

    from media_hygiene.review.http import Request, Response


async def asset_or_page(
    request: Request, page: Callable[[Request], Awaitable[Response]]
) -> Response:
    """Serve a font, an image of the theme or a page of the docs; else the page answers.

    Args:
        request: The request.
        page: How the page served answers.

    Returns:
        The response.
    """
    if not is_local(request):
        return await page(request)
    if request.path.startswith(ASSETS_PREFIX):
        return await asset_response(request.path)
    if request.path.startswith(DOCS_PREFIX):
        return await docs_response(request)
    return await page(request)
