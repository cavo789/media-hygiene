"""A file sent by parts that vanished or shrank ends its body early, quietly."""

from __future__ import annotations

import asyncio
from http import HTTPStatus
from importlib.resources import files
from typing import TYPE_CHECKING, cast

from media_hygiene.review.http import ContentType, FilePart, Response
from media_hygiene.review.respond import RUN_HEADER, RUN_TAG, write_response

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


def test_every_answer_says_the_run_of_its_server() -> None:
    """0354: the run id, the same on each answer of a server, its ETag's value."""
    heads = []
    for response in (Response(HTTPStatus.OK), Response(HTTPStatus.NOT_FOUND)):
        sink = _Sink()
        asyncio.run(write_response(cast("asyncio.StreamWriter", sink), response))
        heads.append(bytes(sink.sent).partition(b"\r\n\r\n")[0].decode())
    line = f"{RUN_HEADER}: {RUN_TAG.strip('"')}"
    assert all(line in head.splitlines() for head in heads)


_WAITING_PAGES = (
    "review/templates/home.js.j2",
    "review/templates/home_link.html.j2",
    "review/templates/apply_now.html.j2",
    "review/templates/phone_review.js.j2",
)


def test_each_page_waiting_for_the_next_server_reads_its_run() -> None:
    """0354: the tab knows the next server by its run id, not only once seen gone.

    The next server may answer 0.5 s after the last one ended (measured on Windows):
    a poll every second missed it, and the tab waited until F5.
    """
    package = files("media_hygiene")
    for name in _WAITING_PAGES:
        assert f'"{RUN_HEADER}"' in package.joinpath(name).read_text("utf-8"), name
    waits = package.joinpath("review/templates/home_run.js.j2").read_text("utf-8")
    assert "now !== run" in waits
    assert "COMEBACK_MS" in waits
