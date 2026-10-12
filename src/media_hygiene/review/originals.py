"""`GET /original/<key>.<ext>`: a shot of the review as it lies on the disk.

The preview is re-encoded; the original is not. Opened in a new tab, it shows that what
the page displays is faithful: a blurred shot is blurred in the file itself. Formats a
browser cannot show (RAW, HEIC, TIFF) are downloaded instead.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import ContentType, Response
from media_hygiene.review.views import ORIGINAL_PREFIX

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

_SHOWN: Final = MappingProxyType(
    {
        ".jpg": ContentType.JPEG,
        ".jpeg": ContentType.JPEG,
        ".png": ContentType.PNG,
        ".gif": ContentType.GIF,
        ".webp": ContentType.WEBP,
    }
)


async def original_response(
    path: str, source_of: Callable[[str], Path | None]
) -> Response:
    """Serve the bytes of a shot, untouched.

    Args:
        path: The path asked for: `/original/<key>.<ext>`.
        source_of: Finds the shot a key names, or None.

    Returns:
        The file, cached by the browser; 404 for an unknown key or a vanished file.
    """
    name = path.removeprefix(ORIGINAL_PREFIX)
    key = name.split(".", 1)[0]
    source = source_of(key)
    if source is None or path != f"{ORIGINAL_PREFIX}{key}{source.suffix.lower()}":
        return Response(HTTPStatus.NOT_FOUND)
    try:
        body = await asyncio.to_thread(source.read_bytes)
    except OSError:
        return Response(HTTPStatus.NOT_FOUND)
    kind = _SHOWN.get(source.suffix.lower(), ContentType.BINARY)
    return Response(HTTPStatus.OK, body, kind, cacheable=True)
