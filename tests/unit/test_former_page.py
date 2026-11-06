"""The Library's address (TODO 0617): `/library`; `/search` leads to it, query kept."""

from __future__ import annotations

import asyncio
from http import HTTPStatus

import pytest

from media_hygiene.review.http import Request, read_request
from media_hygiene.review.lan_paths import phone_may
from media_hygiene.search.app import SEARCH_PAGE_PATH
from media_hygiene.search.former_page import moved_page

_HOST = {"host": "127.0.0.1"}


def _parsed(target: str) -> Request:
    """A request as the server reads it from the socket."""

    async def read() -> Request:
        reader = asyncio.StreamReader()
        reader.feed_data(f"GET {target} HTTP/1.1\r\nHost: 127.0.0.1\r\n\r\n".encode())
        reader.feed_eof()
        return await read_request(reader)

    return asyncio.run(read())


def test_the_page_lives_at_library() -> None:
    """The constant every link is built from."""
    assert SEARCH_PAGE_PATH == "/library"


@pytest.mark.parametrize(
    ("target", "location"),
    [
        ("/search", "/library"),
        ("/search/", "/library"),
        ("/search?folder=a%20b&x=1", "/library?folder=a%20b&x=1"),
        ("/search/deep/er?q=1", "/library/deep/er?q=1"),
    ],
)
def test_the_former_address_redirects_keeping_all(target: str, location: str) -> None:
    """Sub-paths and the query string survive, read from a real request line."""
    answer = moved_page(_parsed(target))
    assert answer is not None
    assert answer.status is HTTPStatus.MOVED_PERMANENTLY
    assert answer.headers == (f"Location: {location}",)


@pytest.mark.parametrize("path", ["/library", "/searching", "/api/search", "/"])
def test_other_paths_are_left_alone(path: str) -> None:
    """Only the former address itself moves, never a path that merely starts alike."""
    assert moved_page(Request("GET", path, _HOST)) is None


def test_a_post_is_never_redirected() -> None:
    """Only a page read moves."""
    assert moved_page(Request("POST", "/search", _HOST)) is None


def test_a_phones_old_bookmark_may_ask() -> None:
    """A paired phone's saved `/search` reaches the redirect, not a refusal."""
    assert phone_may(Request("GET", "/search", _HOST))
    assert phone_may(Request("GET", "/search/x", _HOST))
    assert not phone_may(Request("POST", "/search", _HOST))
