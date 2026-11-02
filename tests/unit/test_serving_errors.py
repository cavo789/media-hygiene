"""An unexpected error while answering: logged with its trace, answered 500."""

from __future__ import annotations

import asyncio
import json
import logging
from typing import TYPE_CHECKING, cast

from media_hygiene.review.serving import serve_connection

if TYPE_CHECKING:
    import pytest

    from media_hygiene.review.http import Request, Response


class _Writer:
    """A connection that keeps what is written."""

    def __init__(self) -> None:
        """Nothing written yet."""
        self.data = b""
        self.closed = False

    def write(self, data: bytes) -> None:
        """Keep the bytes.

        Args:
            data: The bytes written.
        """
        self.data += data

    async def drain(self) -> None:
        """Nothing to flush."""

    def close(self) -> None:
        """Remember the connection was closed."""
        self.closed = True

    async def wait_closed(self) -> None:
        """Closed at once."""


def test_an_unexpected_error_is_answered_and_logged(
    caplog: pytest.LogCaptureFixture,
) -> None:
    """The page reads the error, not a closed connection; the log has the trace."""

    async def scenario() -> _Writer:
        reader = asyncio.StreamReader()
        reader.feed_data(b"POST /api/move HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n")
        reader.feed_eof()
        writer = _Writer()

        async def broken(_request: Request) -> Response:
            message = "boom"
            raise KeyError(message)

        await serve_connection(reader, cast("asyncio.StreamWriter", writer), broken)
        return writer

    with caplog.at_level(logging.ERROR):
        writer = asyncio.run(scenario())
    head, _, body = writer.data.partition(b"\r\n\r\n")
    assert head.startswith(b"HTTP/1.1 500")
    assert "KeyError" in json.loads(body)["error"]
    assert writer.closed
    assert caplog.records[0].exc_info is not None
    assert "/api/move" in caplog.records[0].getMessage()
