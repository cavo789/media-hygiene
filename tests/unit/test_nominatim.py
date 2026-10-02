"""The Nominatim client, never on the network: a fake transport and a fake clock."""

from __future__ import annotations

import asyncio
import json
import urllib.error
import urllib.request
from email.message import Message
from pathlib import Path
from typing import Final
from urllib.parse import parse_qs, urlsplit

import pytest

from media_hygiene.errors import NominatimError
from media_hygiene.geo.nominatim import INTERVAL_S, Nominatim, Service, Transport
from media_hygiene.places.osm_search import online_search

RECORDED: Final = Path(__file__).resolve().parents[1] / "fixtures" / "nominatim"
SERVICE: Final = Service("https://nominatim.example.org/", "fr", "media-hygiene/9 (+x)")


class _Fake:
    """Answers every request with `body` (or raises `error`); time moves on sleep."""

    def __init__(self, body: bytes = b"[]", error: OSError | None = None) -> None:
        """Nothing asked yet, at time 100."""
        self.body = body
        self.error = error
        self.now = 100.0
        self.requests: list[urllib.request.Request] = []
        self.slept: list[float] = []

    def transport(self) -> Transport:
        """The transport the client uses."""
        return Transport(fetch=self.fetch, clock=lambda: self.now, sleep=self.sleep)

    def fetch(self, request: urllib.request.Request, _timeout: float) -> bytes:
        """Record the request, answer."""
        self.requests.append(request)
        if self.error is not None:
            raise self.error
        return self.body

    async def sleep(self, seconds: float) -> None:
        """Let time pass."""
        self.slept.append(seconds)
        self.now += seconds


def _search(client: Nominatim, *texts: str) -> list[int]:
    """Search each text in turn; the number of areas found for each."""

    async def scenario() -> list[int]:
        return [len((await client.search(text)).areas) for text in texts]

    return asyncio.run(scenario())


def test_the_request_identifies_the_tool_and_asks_for_outlines() -> None:
    """User-Agent, language, jsonv2, GeoJSON outlines, simplified; the text alone."""
    fake = _Fake((RECORDED / "search.json").read_bytes())
    client = Nominatim(SERVICE, fake.transport())
    assert _search(client, "  Fictiville ") == [2]
    request = fake.requests[0]
    assert request.get_header("User-agent") == "media-hygiene/9 (+x)"
    assert request.get_header("Accept-language") == "fr"
    url = urlsplit(request.full_url)
    assert (url.netloc, url.path) == ("nominatim.example.org", "/search")
    query = parse_qs(url.query)
    assert query["q"] == ["fictiville"]
    assert query["format"] == ["jsonv2"]
    assert query["polygon_geojson"] == ["1"]
    assert "polygon_threshold" in query
    assert client.host == "nominatim.example.org"


def test_the_same_text_is_asked_once() -> None:
    """The policy: results cached, a repeated query never sent again."""
    fake = _Fake()
    client = Nominatim(SERVICE, fake.transport())
    _search(client, "Fictiville", "fictiville", "FICTIVILLE")
    assert len(fake.requests) == 1


def test_two_searches_within_a_second_are_spaced_out() -> None:
    """The second waits for the rest of the second; a later one does not wait."""
    fake = _Fake()
    client = Nominatim(SERVICE, fake.transport())
    _search(client, "one")
    fake.now += 0.25
    _search(client, "two")
    assert fake.slept == [pytest.approx(INTERVAL_S - 0.25)]
    fake.now += 5
    _search(client, "three")
    assert len(fake.slept) == 1
    assert len(fake.requests) == 3


def _http_error(status: int) -> urllib.error.HTTPError:
    """An HTTP error answer."""
    return urllib.error.HTTPError("https://x", status, "no", Message(), None)


@pytest.mark.parametrize(
    ("error", "said"),
    [
        (urllib.error.URLError("no route"), "Cannot reach nominatim.example.org"),
        (TimeoutError(), "offline"),
        (_http_error(429), "usage limits"),
        (_http_error(403), "nominatim_url"),
        (_http_error(500), "error 500"),
    ],
)
def test_a_failed_request_says_why(error: OSError, said: str) -> None:
    """Offline, refused, broken: a sentence, never a traceback."""
    client = Nominatim(SERVICE, _Fake(error=error).transport())
    with pytest.raises(NominatimError, match=said):
        _search(client, "Fictiville")


@pytest.mark.parametrize("body", [b"<html>", json.dumps({"a": 1}).encode()])
def test_an_answer_that_is_not_results_is_refused(body: bytes) -> None:
    """HTML or another JSON shape."""
    client = Nominatim(SERVICE, _Fake(body).transport())
    with pytest.raises(NominatimError, match="not a search result"):
        _search(client, "Fictiville")


def test_an_empty_address_means_no_online_search() -> None:
    """`[places] nominatim_url = ""`."""
    assert online_search("") is None
    client = online_search("https://nominatim.example.org")
    assert client is not None
    assert client.service.agent.startswith("media-hygiene/")
    assert "github.com/cavo789/media-hygiene" in client.service.agent
    assert client.service.language == "en"
