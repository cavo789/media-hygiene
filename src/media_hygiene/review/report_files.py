"""`GET /reports/<path>`: the reports folder, served by the home page.

A browser does not open a `file://` link from a page served over HTTP: the reports and
their previews are served by the page's own server instead, read-only, never outside
the reports folder.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final
from urllib.parse import unquote

from media_hygiene.constants import REPORT_INDEX_FILE_NAME
from media_hygiene.review.home_views import REPORTS_PREFIX
from media_hygiene.review.http import ContentType, Response

if TYPE_CHECKING:
    from pathlib import Path

_SERVED: Final = MappingProxyType(
    {
        ".html": ContentType.HTML,
        ".jpg": ContentType.JPEG,
        ".jpeg": ContentType.JPEG,
        ".png": ContentType.PNG,
        ".webp": ContentType.WEBP,
        ".json": ContentType.JSON,
        ".csv": ContentType.TEXT,
        ".txt": ContentType.TEXT,
    }
)


def report_file(reports_dir: Path, path: str) -> Path | None:
    """Find the file a `/reports/…` path names, inside the reports folder only.

    Args:
        reports_dir: The reports folder, in the container.
        path: The path asked for; `/reports/` alone is `index.html`.

    Returns:
        The file, or None when it is outside the folder or missing.
    """
    relative = unquote(path.removeprefix(REPORTS_PREFIX)) or REPORT_INDEX_FILE_NAME
    root = reports_dir.resolve()
    target = (root / relative).resolve()
    if not target.is_relative_to(root) or not target.is_file():
        return None
    return target


async def report_response(reports_dir: Path, path: str) -> Response:
    """Serve a file of the reports folder, as it lies on the disk.

    Args:
        reports_dir: The reports folder, in the container.
        path: The path asked for.

    Returns:
        The file; 404 outside the folder, for a missing or unreadable file.
    """
    target = report_file(reports_dir, path)
    if target is None:
        return Response(HTTPStatus.NOT_FOUND)
    try:
        body = await asyncio.to_thread(target.read_bytes)
    except OSError:
        return Response(HTTPStatus.NOT_FOUND)
    kind = _SERVED.get(target.suffix.lower(), ContentType.BINARY)
    return Response(HTTPStatus.OK, body, kind)
