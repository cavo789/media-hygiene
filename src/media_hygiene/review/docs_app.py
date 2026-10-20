"""`GET /docs/<locale>/…`: the documentation of the version that runs, offline (0270).

`/docs/<locale>/<page>/` is a page inside the home page's shell (`docs/view.py`),
`/docs/<locale>/images/<name>` a screenshot, `/docs/<locale>/index.json` the index the
home page's palette searches. Read from the docs rendered when the image was built
(`docs/shelf.py`); without them, 404: the links then point at the public site.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from media_hygiene.constants import Locale
from media_hygiene.docs.pages import DOCS_PREFIX, IMAGES_DIR, INDEX_FILE
from media_hygiene.docs.shelf import doc_index, docs_root
from media_hygiene.docs.view import DocView, render_doc_page
from media_hygiene.review.home_assets import MAX_AGE_S, asset_file
from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.report_files import read_found

if TYPE_CHECKING:
    from pathlib import Path

    from media_hygiene.review.http import Request

_GET: Final = "GET"
_IMAGES: Final = f"{IMAGES_DIR}/"
_SCREENSHOTS: Final = MappingProxyType(
    {".webp": ContentType.WEBP, ".png": ContentType.PNG}
)


async def docs_response(request: Request) -> Response:
    """Answer a request for the docs.

    Args:
        request: `GET /docs/…`.

    Returns:
        The page, screenshot or index; 404 for anything else, or without docs.
    """
    if request.method != _GET:
        return Response(HTTPStatus.METHOD_NOT_ALLOWED)
    root = await asyncio.to_thread(docs_root)
    language, _slash, tail = unquote(request.path.removeprefix(DOCS_PREFIX)).partition(
        "/"
    )
    if root is None or language not in Locale:
        return Response(HTTPStatus.NOT_FOUND)
    locale = Locale(language)
    if tail.startswith(_IMAGES):
        return await _screenshot(root / language / IMAGES_DIR, tail)
    if tail == INDEX_FILE:
        body = await read_found(root / language / INDEX_FILE)
        if body is None:  # pragma: no cover - docs_root checked the English one
            return Response(HTTPStatus.NOT_FOUND)
        return Response(HTTPStatus.OK, body, ContentType.JSON)
    index = await asyncio.to_thread(doc_index, root, locale)
    page = index.at_route(f"{DOCS_PREFIX}{language}/{tail}")
    body = await asyncio.to_thread(render_doc_page, DocView(root, locale, page))
    status = HTTPStatus.OK if page else HTTPStatus.NOT_FOUND
    return Response(status, body, ContentType.HTML)


async def _screenshot(folder: Path, tail: str) -> Response:
    """Serve a screenshot of the docs, kept a day by the browser.

    Args:
        folder: The screenshots of the language.
        tail: `images/<name>`.

    Returns:
        The image; 404 outside the folder, missing, or of another type.
    """
    target = asset_file(tail.removeprefix(_IMAGES), folder)
    kind = _SCREENSHOTS.get(target.suffix.lower()) if target else None
    body = await read_found(target if kind else None)
    if kind is None or body is None:
        return Response(HTTPStatus.NOT_FOUND)
    return Response(HTTPStatus.OK, body, kind, max_age=MAX_AGE_S)
