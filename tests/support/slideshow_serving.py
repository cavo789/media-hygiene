"""The home server's slideshow over a test index, and the requests its pages send."""

from __future__ import annotations

import asyncio
import contextlib
import json
from concurrent.futures import ThreadPoolExecutor
from typing import TYPE_CHECKING, Final

from media_hygiene.review.ending import Ending
from media_hygiene.review.http import Request, Response
from media_hygiene.search.fts import SearchIndex
from media_hygiene.services import slideshow_here
from media_hygiene.services.fresh_runtime import FreshRuntime
from media_hygiene.services.home_pages import HomeServer
from media_hygiene.services.slideshow_here import SlideshowHere

if TYPE_CHECKING:
    from collections.abc import Iterator, Mapping
    from pathlib import Path

    import pytest

    from media_hygiene.services.runtime import Runtime

HOST: Final = {"host": "127.0.0.1:8088", "content-type": "application/json"}


def search_in(monkeypatch: pytest.MonkeyPatch, index: Path) -> None:
    """Make the slideshow search this index file (no words index).

    Args:
        monkeypatch: The test's patcher.
        index: The index file.
    """

    @contextlib.contextmanager
    def opened(_runtime: Runtime, *, words: bool) -> Iterator[SearchIndex]:
        assert not words
        with SearchIndex.open(index) as search:
            yield search

    monkeypatch.setattr(slideshow_here, "open_search", opened)


def slideshow_of(runtime: Runtime) -> Iterator[SlideshowHere]:
    """The home server's slideshow, closed at the end (a fixture's `yield from`).

    Args:
        runtime: The runtime.

    Yields:
        The slideshow.
    """
    with ThreadPoolExecutor(1) as executor:
        built = SlideshowHere(
            FreshRuntime(runtime), HomeServer(None, Ending(), executor)
        )
        yield built
        built.close()


def ask(here: SlideshowHere, request: Request) -> Response:
    """Answer one request.

    Args:
        here: The slideshow.
        request: The request.

    Returns:
        The answer.
    """
    return asyncio.run(here.handle(request))


def choose(here: SlideshowHere, body: Mapping[str, object]) -> Response:
    """Post the home's TV choices.

    Args:
        here: The slideshow.
        body: The choices.

    Returns:
        The answer.
    """
    payload = json.dumps(body).encode()
    return ask(here, Request("POST", "/slideshow/choose", HOST, payload))


def shown(here: SlideshowHere) -> list[int]:
    """The keys of the slides, in show order.

    Args:
        here: The slideshow.

    Returns:
        The keys.
    """
    answer = ask(here, Request("GET", "/slideshow/api/slides", HOST))
    return [slide["key"] for slide in json.loads(answer.body)["slides"]]
