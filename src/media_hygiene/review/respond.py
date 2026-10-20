"""Send a response: its head, then its body, or a part of a file in chunks.

A video is never read whole: the browser asks for it piece by piece (`Range`), and
each piece is read and sent a chunk at a time, waiting for the browser to take it.

A picture is named by a number valid in this run only: `/face/3.jpg` is another face
once the command runs again, on the same port. So the browser keeps it but asks again
each time (`no-cache`), and `RUN_TAG`, drawn anew at each run, says whether its copy is
still this run's (304, nothing rendered) or an older run's (rendered again).
"""

from __future__ import annotations

import asyncio
import secrets
from http import HTTPStatus
from typing import TYPE_CHECKING, Final

from media_hygiene.review.http import HEADER_ENCODING

if TYPE_CHECKING:
    from media_hygiene.review.http import FilePart, Response

CHUNK: Final = 256 * 1024
RUN_TAG: Final = f'"{secrets.token_hex(8)}"'  # the ETag of every cacheable answer


async def write_response(writer: asyncio.StreamWriter, response: Response) -> None:
    """Send a response; the connection is closed by the caller.

    Args:
        writer: The connection.
        response: What to send.
    """
    status = response.status
    cache = (
        (f"private, max-age={response.max_age}",)
        if response.max_age
        else ("private, no-cache", f"ETag: {RUN_TAG}")
        if response.cacheable
        else ("no-store",)
    )
    part = response.part
    length = len(response.body) if part is None else part.length
    head = (
        f"HTTP/1.1 {status.value} {status.phrase}",
        f"Content-Type: {response.content_type}",
        f"Content-Length: {length}",
        f"Cache-Control: {cache[0]}",
        *cache[1:],
        "Connection: close",
        "X-Content-Type-Options: nosniff",
        f"Referrer-Policy: {response.referrer}",
        f"Content-Security-Policy: {response.policy}",
        *_range_head(status, part),
    )
    writer.write(("\r\n".join(head) + "\r\n\r\n").encode(HEADER_ENCODING))
    writer.write(response.body)
    await writer.drain()
    if part is not None and part.length:
        await _send_part(writer, part)


def _range_head(status: HTTPStatus, part: FilePart | None) -> tuple[str, ...]:
    """The header lines of a file sent by parts.

    Args:
        status: 200 (whole), 206 (a part) or 416 (a part beyond the end).
        part: The part, or None for any other response.

    Returns:
        `Accept-Ranges`, and `Content-Range` for 206 and 416.
    """
    if part is None:
        return ()
    accept = "Accept-Ranges: bytes"
    if status is HTTPStatus.PARTIAL_CONTENT:
        last = part.start + part.length - 1
        return accept, f"Content-Range: bytes {part.start}-{last}/{part.size}"
    if status is HTTPStatus.REQUESTED_RANGE_NOT_SATISFIABLE:
        return accept, f"Content-Range: bytes */{part.size}"
    return (accept,)


async def _send_part(writer: asyncio.StreamWriter, part: FilePart) -> None:
    """Read the part a chunk at a time, in a thread, and send each chunk.

    A file that vanished or shrank since its size was read ends the body early: the
    browser sees a short answer, and the connection is closed.

    Args:
        writer: The connection.
        part: What to send.
    """
    try:
        source = await asyncio.to_thread(part.path.open, "rb")
    except OSError:
        return
    with source:
        await asyncio.to_thread(source.seek, part.start)
        left = part.length
        while left > 0:
            try:
                chunk = await asyncio.to_thread(source.read, min(CHUNK, left))
            except OSError:
                return
            if not chunk:
                return
            writer.write(chunk)
            await writer.drain()
            left -= len(chunk)
