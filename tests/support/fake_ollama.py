"""A fake Ollama server: asyncio streams in a thread, scripted answers, calls recorded.

It describes a picture from its average colour (blue: a beach, white: snow, else a
cake) and maps a description to the first category sharing a keyword with it.
"""

from __future__ import annotations

import asyncio
import base64
import io
import json
import re
import threading
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final, Self

from PIL import Image, ImageStat

if TYPE_CHECKING:
    from collections.abc import Callable

_LOOPBACK: Final = "127.0.0.1"
_NUMBERED: Final = re.compile(r"^\d+\. (?P<text>.+)$", re.MULTILINE)
_BRIGHT: Final = 200
KEYWORDS: Final = {"beach": "Holidays", "snow": "Nature", "cake": "Parties"}


@dataclass
class FakeOllama:
    """A scripted Ollama: what it can do, how it fails, what it was asked."""

    capabilities: tuple[str, ...] = ("completion", "vision")
    chat_status: int = 200
    answer: Callable[[dict[str, object]], dict[str, object]] | None = None
    calls: list[tuple[str, dict[str, object]]] = field(default_factory=list)
    url: str = ""
    _running: (
        tuple[asyncio.AbstractEventLoop, asyncio.Server, threading.Thread] | None
    ) = None

    def described(self) -> int:
        """Count the photos sent so far."""
        return sum(
            1 for path, body in self.calls if path == "/api/chat" and images(body)
        )

    def mapped(self) -> int:
        """Count the mapping calls so far."""
        return sum(
            1 for path, body in self.calls if path == "/api/chat" and not images(body)
        )

    def __enter__(self) -> Self:
        """Start serving on a free loopback port."""
        loop = asyncio.new_event_loop()
        server = loop.run_until_complete(
            asyncio.start_server(self._serve, _LOOPBACK, 0)
        )
        port = server.sockets[0].getsockname()[1]
        self.url = f"http://{_LOOPBACK}:{port}"
        thread = threading.Thread(target=loop.run_forever, daemon=True)
        thread.start()
        self._running = (loop, server, thread)
        return self

    def __exit__(self, *exc_info: object) -> None:
        """Stop serving."""
        if self._running is None:
            return
        loop, server, thread = self._running
        loop.call_soon_threadsafe(loop.stop)
        thread.join()
        server.close()
        loop.run_until_complete(server.wait_closed())
        loop.close()

    async def _serve(
        self, reader: asyncio.StreamReader, writer: asyncio.StreamWriter
    ) -> None:
        """Answer one request, then close."""
        request = (await reader.readline()).decode().split()
        length = 0
        while (line := (await reader.readline()).decode().strip()) != "":
            name, _sep, value = line.partition(":")
            if name.casefold() == "content-length":
                length = int(value)
        body = json.loads(await reader.readexactly(length))
        self.calls.append((request[1], body))
        status, answer = self._route(request[1], body)
        payload = json.dumps(answer).encode()
        head = f"HTTP/1.1 {status} X\r\nContent-Length: {len(payload)}\r\n"
        writer.write(f"{head}Connection: close\r\n\r\n".encode() + payload)
        await writer.drain()
        writer.close()

    def _route(
        self, path: str, body: dict[str, object]
    ) -> tuple[int, dict[str, object]]:
        """The status and answer of one request."""
        if path == "/api/show":
            if body.get("model") == "missing":
                return 404, {"error": "model not found"}
            return 200, {"capabilities": list(self.capabilities)}
        if self.chat_status != 200:
            return self.chat_status, {"error": "scripted failure"}
        if self.answer is not None:
            return 200, {"message": {"content": json.dumps(self.answer(body))}}
        content = describe(body) if images(body) else map_answer(body)
        return 200, {"message": {"role": "assistant", "content": json.dumps(content)}}


def images(body: dict[str, object]) -> list[str]:
    """The pictures of a chat request."""
    messages = body.get("messages")
    assert isinstance(messages, list)
    images = messages[0].get("images", [])
    assert isinstance(images, list)
    return images


def describe(body: dict[str, object]) -> dict[str, object]:
    """Describe a picture from its average colour."""
    data = base64.b64decode(images(body)[0])
    with Image.open(io.BytesIO(data)) as picture:
        red, green, blue = ImageStat.Stat(picture.convert("RGB")).mean
    if min(red, green, blue) > _BRIGHT:
        return {"description": "Snow on a mountain.", "tags": ["snow"]}
    if blue > red:
        return {"description": "A beach by the sea.", "tags": ["beach", "sea"]}
    return {"description": "A birthday cake.", "tags": ["cake"]}


def map_answer(body: dict[str, object]) -> dict[str, object]:
    """Choose a category per numbered description."""
    messages = body.get("messages")
    assert isinstance(messages, list)
    content = str(messages[0]["content"])
    schema = json.dumps(body["format"])
    choices = json.loads(schema)["properties"]["categories"]["items"]["enum"]
    found = []
    for match in _NUMBERED.finditer(content):
        text = match["text"].casefold()
        word = next((w for w in KEYWORDS if w in text), None)
        hit = [c for c in choices if word and c.startswith(KEYWORDS[word])]
        found.append(hit[0] if hit else "none")
    return {"categories": found}
