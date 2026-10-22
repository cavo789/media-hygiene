"""`GET /video/<key>.<ext>`: a video of `review --near`, played in the page.

Only the versions of the plan's groups are served, as the originals are, and only in
a format a browser can play. The browser asks for the video piece by piece (`Range`)
to read its length, then to seek: each piece is answered `206 Partial Content` and
streamed from the disk, never read whole.
"""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from types import MappingProxyType
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import REVIEW_POLICY, ContentType, FilePart, Response

if TYPE_CHECKING:
    from collections.abc import Callable
    from pathlib import Path

    from media_hygiene.review.http import Request

VIDEO_PREFIX: Final = "/video/"
_IMAGES: Final = "img-src 'self';"
# The near page plays its videos too; the burst page keeps the stricter policy.
NEAR_POLICY: Final = REVIEW_POLICY.replace(_IMAGES, f"{_IMAGES} media-src 'self';")
_BYTES: Final = "bytes="
_PLAYED: Final = MappingProxyType(
    {
        ".mp4": ContentType.MP4,
        ".m4v": ContentType.MP4,
        ".mov": ContentType.QUICKTIME,
        ".mkv": ContentType.MATROSKA,
        ".3gp": ContentType.THREE_GPP,
        ".3g2": ContentType.THREE_GPP2,
    }
)


def video_path(key: str, source: Path) -> str:
    """The address the page plays a video from.

    Args:
        key: The version's key.
        source: The version, in the container.

    Returns:
        `/video/<key>.<ext>`; empty for a format a browser cannot play (AVI, FLV…).
    """
    suffix = source.suffix.lower()
    return f"{VIDEO_PREFIX}{key}{suffix}" if suffix in _PLAYED else ""


async def video_response(
    request: Request, source_of: Callable[[str], Path | None]
) -> Response:
    """Serve a video, whole or the part the browser asks for.

    Args:
        request: `GET /video/<key>.<ext>`, with or without a `Range` header.
        source_of: Finds the version a key names, or None.

    Returns:
        200 (whole) or 206 (a part), sent in chunks; 416 for a part beyond the end;
        404 for an unknown key, a format that cannot be played or a vanished file.
    """
    key = request.path.removeprefix(VIDEO_PREFIX).split(".", 1)[0]
    source = source_of(key)
    if source is None or request.path != video_path(key, source):
        return Response(HTTPStatus.NOT_FOUND)
    return await streamed(request, source, _PLAYED[source.suffix.lower()])


async def streamed(
    request: Request, source: Path, content_type: ContentType
) -> Response:
    """Send a video from the disk, whole or the part the `Range` header asks for.

    Args:
        request: The request, with or without a `Range` header.
        source: The video, in the container.
        content_type: The type the browser plays it by.

    Returns:
        200 (whole) or 206 (a part), sent in chunks; 416 for a part beyond the end;
        404 for a vanished file.
    """
    try:
        size = (await asyncio.to_thread(source.stat)).st_size
    except OSError:
        return Response(HTTPStatus.NOT_FOUND)
    status, start, length = asked_part(request.headers.get("range", ""), size)
    return Response(
        status,
        content_type=content_type,
        cacheable=True,
        policy=NEAR_POLICY,
        part=FilePart(source, start, length, size),
    )


def asked_part(header: str, size: int) -> tuple[HTTPStatus, int, int]:
    """Read a `Range` header: one range of bytes, from a start or from the end.

    A header that is missing, malformed or asks for several ranges is ignored: the
    whole file is sent, as HTTP allows.

    Args:
        header: The header's value (empty without one).
        size: The size of the file.

    Returns:
        The status, the first byte and the number of bytes to send.
    """
    whole = (HTTPStatus.OK, 0, size)
    value = header.strip()
    first, dash, last = value.removeprefix(_BYTES).partition("-")
    if not value.startswith(_BYTES) or not dash or not (first or last):
        return whole
    if not (first or "0").isdigit() or not (last or "0").isdigit():
        return whole
    if last and first and int(last) < int(first):
        return whole
    start = int(first) if first else max(size - int(last), 0)  # `bytes=-500`: the end
    end = min(int(last), size - 1) if first and last else size - 1
    if start >= size:
        return HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE, 0, 0
    return HTTPStatus.PARTIAL_CONTENT, start, end - start + 1
