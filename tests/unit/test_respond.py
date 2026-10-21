"""A file sent by parts that vanished or shrank ends its body early, quietly."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from typing import TYPE_CHECKING, cast

from media_hygiene.review.http import ContentType, FilePart, Response
from media_hygiene.review.respond import write_response

if TYPE_CHECKING:
    from pathlib import Path


class _Sink:
    """Stands for the connection: keeps what is written."""

    def __init__(self) -> None:
        """Start empty."""
        self.sent = bytearray()

    def write(self, data: bytes) -> None:
        """Keep the bytes."""
        self.sent += data

    async def drain(self) -> None:
        """Nothing to wait for."""


def _send(part: FilePart) -> bytes:
    """Send a 206 for `part`; return what reached the connection, after the head."""
    sink = _Sink()
    response = Response(
        HTTPStatus.PARTIAL_CONTENT, content_type=ContentType.MP4, part=part
    )
    asyncio.run(write_response(cast("asyncio.StreamWriter", sink), response))
    head, _blank, body = bytes(sink.sent).partition(b"\r\n\r\n")
    assert b"Content-Range: bytes" in head
    return body


def test_a_vanished_file_sends_no_body(tmp_path: Path) -> None:
    """The head is gone already; the body is simply empty."""
    assert _send(FilePart(tmp_path / "gone.mp4", 0, 10, 10)) == b""


def test_a_shrunk_file_sends_what_is_left(tmp_path: Path) -> None:
    """Fewer bytes than announced: what the file still holds, then the end."""
    video = tmp_path / "short.mp4"
    video.write_bytes(b"0123456789")
    assert _send(FilePart(video, 4, 100, 100)) == b"456789"


def test_the_extra_headers_are_sent() -> None:
    """`Location` and `Set-Cookie` reach the browser (0269: a phone paired)."""
    sink = _Sink()
    response = Response(
        HTTPStatus.SEE_OTHER, headers=("Location: /", "Set-Cookie: a=b")
    )
    asyncio.run(write_response(cast("asyncio.StreamWriter", sink), response))
    head = bytes(sink.sent).partition(b"\r\n\r\n")[0]
    assert b"\r\nLocation: /" in head
    assert b"\r\nSet-Cookie: a=b" in head
