"""`[places]`: the tile server of the map, and the one host the page may load from."""

from __future__ import annotations

import asyncio
from typing import cast

import pytest
from pydantic import ValidationError

from media_hygiene.config.places_settings import PlacesSettings
from media_hygiene.review.serving import serve_connection


def test_the_default_tiles_are_openstreetmap() -> None:
    """Their host is the only one the page's policy allows."""
    assert PlacesSettings().tile_host == "https://tile.openstreetmap.org"


def test_subdomains_are_allowed_as_a_wildcard() -> None:
    """`{s}.tile.example.org` serves from a, b, c and so on."""
    settings = PlacesSettings(tiles="https://{s}.tile.example.org/{z}/{x}/{y}.png")
    assert settings.tile_host == "https://*.tile.example.org"


@pytest.mark.parametrize(
    "tiles",
    ["http://tile.example.org/{z}/{x}/{y}.png", "https://tile.example.org/{z}/{x}.png"],
)
def test_a_tile_address_must_be_https_with_z_x_y(tiles: str) -> None:
    """Refused at load time."""
    with pytest.raises(ValidationError):
        PlacesSettings(tiles=tiles)


def test_the_online_search_is_openstreetmap_unless_emptied() -> None:
    """Another instance, or none at all."""
    assert PlacesSettings().nominatim_url == "https://nominatim.openstreetmap.org"
    assert not PlacesSettings(nominatim_url=" ").nominatim_url
    local = PlacesSettings(nominatim_url="http://nominatim.lan:8080")
    assert local.nominatim_url == "http://nominatim.lan:8080"


@pytest.mark.parametrize("url", ["ftp://nominatim.example.org", "nominatim"])
def test_a_search_address_must_be_a_web_address(url: str) -> None:
    """Refused at load time."""
    with pytest.raises(ValidationError, match="http"):
        PlacesSettings(nominatim_url=url)


class _Writer:
    """Just enough of a stream writer."""

    def __init__(self) -> None:
        """Nothing written yet."""
        self.closed = False

    def write(self, _data: bytes) -> None:
        """Ignore what is written."""

    async def drain(self) -> None:
        """Nothing to flush."""

    def close(self) -> None:
        """Remember the connection was closed."""
        self.closed = True

    async def wait_closed(self) -> None:
        """Closed at once."""


def test_a_browser_that_goes_away_gets_no_answer() -> None:
    """A body cut short: nothing is answered, the connection is closed."""

    async def scenario() -> _Writer:
        reader = asyncio.StreamReader()
        reader.feed_data(
            b"POST / HTTP/1.1\r\nHost: 127.0.0.1\r\nContent-Length: 9\r\n\r\nab"
        )
        reader.feed_eof()
        writer = _Writer()

        async def never(_request: object) -> object:
            raise AssertionError

        await serve_connection(
            reader,
            cast("asyncio.StreamWriter", writer),
            never,  # type: ignore[arg-type]
        )
        return writer

    assert asyncio.run(scenario()).closed
