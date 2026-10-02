"""Search OpenStreetMap's Nominatim for an area by its name, as its usage policy asks.

Only the text the user typed is sent: never a photo nor a position. One request per
second at most, an identifying User-Agent, every answer kept for the session (the
same text is never asked twice), no auto-complete: the page asks on a click only.
The standard library's `urllib`, in a thread: no new dependency.
Policy: https://operations.osmfoundation.org/policies/nominatim/
"""

from __future__ import annotations

import asyncio
import json
import time
import urllib.request
from dataclasses import dataclass, field
from typing import TYPE_CHECKING, Final
from urllib.parse import urlencode, urlsplit

from media_hygiene.geo.nominatim_errors import failed, unexpected
from media_hygiene.geo.osm_results import Found, read_results

if TYPE_CHECKING:
    from collections.abc import Awaitable, Callable

type Fetcher = Callable[[urllib.request.Request, float], bytes]

SEARCH: Final = "/search"
INTERVAL_S: Final = 1.0  # the policy: one request per second at most
TIMEOUT_S: Final = 10.0
LIMIT: Final = 8
THRESHOLD_DEGREES: Final = 0.0005  # outlines simplified to about 50 m
MAX_BYTES: Final = 8 * 1024 * 1024


def fetch(request: urllib.request.Request, timeout: float) -> bytes:
    """Send a request and read the answer.

    Args:
        request: The request.
        timeout: Seconds before giving up.

    Returns:
        The body of the answer, at most `MAX_BYTES`.
    """
    # The address is http(s) only: checked when the settings are read.
    with urllib.request.urlopen(request, timeout=timeout) as answer:  # noqa: S310
        return bytes(answer.read(MAX_BYTES))


@dataclass(frozen=True, slots=True)
class Service:
    """Which Nominatim to ask, in which language, and who asks."""

    url: str  # e.g. https://nominatim.openstreetmap.org
    language: str  # e.g. "fr": the names are written in it
    agent: str  # e.g. "media-hygiene/0.3.0 (+https://github.com/...)"


@dataclass(frozen=True, slots=True)
class Transport:
    """How requests are sent and spaced: replaced in tests, never the network there."""

    fetch: Fetcher = fetch
    clock: Callable[[], float] = time.monotonic
    sleep: Callable[[float], Awaitable[None]] = asyncio.sleep


@dataclass(slots=True)
class _Memory:
    """What the session already asked, and when it last asked."""

    answers: dict[str, Found] = field(default_factory=dict)
    last: float | None = None
    lock: asyncio.Lock = field(default_factory=asyncio.Lock)


class Nominatim:
    """Finds areas by name, one request per second at most, each text asked once."""

    def __init__(self, service: Service, transport: Transport | None = None) -> None:
        """Prepare the searches.

        Args:
            service: The instance, the language, the User-Agent.
            transport: How to send and space the requests.
        """
        self.service = service
        self._transport = transport or Transport()
        self._memory = _Memory()

    @property
    def host(self) -> str:
        """The host the searches go to, to tell the user.

        Returns:
            E.g. `nominatim.openstreetmap.org`.
        """
        return urlsplit(self.service.url).netloc

    async def search(self, text: str) -> Found:
        """Find the areas a name designates.

        Args:
            text: What the user typed.

        Returns:
            The areas, the most relevant first.

        Raises:
            NominatimError: The service is unreachable, refused, or answered nonsense.
        """
        key = " ".join(text.split()).casefold()
        memory = self._memory
        async with memory.lock:
            if key in memory.answers:
                return memory.answers[key]
            await self._wait()
            try:
                body = await asyncio.to_thread(
                    self._transport.fetch, self._request(key), TIMEOUT_S
                )
            except OSError as exc:  # URLError, HTTPError and timeouts included
                raise failed(self.host, exc) from exc
            finally:
                memory.last = self._transport.clock()
            memory.answers[key] = self._read(body)
            return memory.answers[key]

    async def _wait(self) -> None:
        """Wait until a second has passed since the last request."""
        last = self._memory.last
        if last is not None:
            wait = last + INTERVAL_S - self._transport.clock()
            if wait > 0:
                await self._transport.sleep(wait)

    def _request(self, text: str) -> urllib.request.Request:
        """The request for one text.

        Args:
            text: What the user typed, normalised.

        Returns:
            The request.
        """
        query = urlencode(
            {
                "q": text,
                "format": "jsonv2",
                "polygon_geojson": 1,
                "polygon_threshold": THRESHOLD_DEGREES,
                "limit": LIMIT,
            }
        )
        headers = {
            "User-Agent": self.service.agent,
            "Accept-Language": self.service.language,
        }
        url = f"{self.service.url.rstrip('/')}{SEARCH}?{query}"
        return urllib.request.Request(url, headers=headers)  # noqa: S310 - http(s)

    def _read(self, body: bytes) -> Found:
        """Read an answer.

        Args:
            body: Its JSON.

        Returns:
            The areas.

        Raises:
            NominatimError: It is not a list of results.
        """
        try:
            return read_results(json.loads(body))
        except (ValueError, TypeError) as exc:
            raise unexpected(self.host) from exc
